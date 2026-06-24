from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import requests
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    HPMSConditionSnapshot,
    HPMSFieldCatalog,
    HPMSInventorySource,
    HPMSLayerCatalog,
    HPMSRoadSegment,
    HighwayRoute,
    RouteSegmentMatch,
)

STATE_CODES = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "puerto rico": "PR",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}

FIELD_HINTS = {
    "external_segment_id": ["objectid", "object_id", "segmentid", "segment_id", "id", "route_id", "link_id"],
    "source_record_id": ["record_id", "inventory_id", "featureid", "feature_id"],
    "state_name": ["state", "state_name", "st"],
    "county_name": ["county", "county_name"],
    "route_name": ["route_name", "routename", "facility_name", "road_name"],
    "route_number": ["route_number", "route_num", "route", "routeid", "route_no", "route_signing"],
    "route_type": ["route_type", "facility_type", "system", "route_system"],
    "functional_class": ["functional_class", "func_class", "f_system", "fclass"],
    "is_nhs": ["nhs", "nhs_ind", "on_nhs", "nhs_flag"],
    "is_interstate": ["interstate", "is_interstate"],
    "urban_code": ["urban_code", "urbanized", "urban"],
    "start_measure": ["begin_milepost", "from_measure", "from_mp", "begin_mp", "start_mp", "frommilepost"],
    "end_measure": ["end_milepost", "to_measure", "to_mp", "end_mp", "endmilepost"],
    "length_miles": ["length", "length_miles", "miles", "section_length", "segment_length"],
    "iri": ["iri", "iri_value", "roughness", "pavement_roughness", "iri_ir"],
    "surface_type": ["surface_type", "surface", "surface_material"],
    "pavement_type": ["pavement_type", "pavement", "pvmt_type"],
    "aadt": ["aadt", "annual_avg_daily_traffic"],
    "truck_aadt": ["truck_aadt", "aadt_truck", "truck_traffic"],
    "lane_count": ["lanes", "lane_count", "through_lanes"],
    "year_recorded": ["year", "data_year", "inventory_year", "year_recorded"],
    "mid_latitude": ["latitude", "lat", "center_lat", "mid_lat"],
    "mid_longitude": ["longitude", "lon", "long", "center_lon", "mid_lon"],
}


def _normalize_token(value) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _pick_value(row: dict, aliases: list[str]):
    normalized = {_normalize_token(key): key for key in row.keys()}
    for alias in aliases:
        original_key = normalized.get(_normalize_token(alias))
        if original_key:
            value = row.get(original_key)
            if value not in (None, ""):
                return value
    return None


def _to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _to_int(value):
    numeric = _to_float(value)
    return int(numeric) if numeric is not None else None


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "t", "yes", "y", "si", "s"}


def _normalize_name(value) -> str:
    return " ".join(str(value or "").strip().split())


def _infer_state_code(state_name: str) -> str:
    return STATE_CODES.get(str(state_name or "").strip().lower(), "")


def _classify_iri(iri_value: float | None) -> str:
    if iri_value is None:
        return ""
    if iri_value < 95:
        return "LOW"
    if iri_value < 170:
        return "MEDIUM"
    if iri_value < 220:
        return "HIGH"
    return "CRITICAL"


def _condition_score_from_iri(iri_value: float | None) -> float:
    if iri_value is None:
        return 0.0
    if iri_value <= 60:
        return 100.0
    return max(5.0, round(100 - ((iri_value - 60) * 0.45), 2))


def _route_adjustment_from_iri(iri_value: float | None) -> float:
    if iri_value is None:
        return 0.0
    if iri_value < 95:
        return 0.0
    if iri_value < 170:
        return 0.05
    if iri_value < 220:
        return 0.12
    return 0.2


def _extract_midpoint_from_geometry(geometry):
    if not geometry:
        return None, None
    coords = geometry.get("coordinates")
    if not coords:
        return None, None
    if geometry.get("type") == "Point" and len(coords) >= 2:
        return coords[1], coords[0]
    if geometry.get("type") == "LineString" and coords:
        mid = coords[len(coords) // 2]
        if len(mid) >= 2:
            return mid[1], mid[0]
    return None, None


class RouteService:
    @staticmethod
    def get_routes_by_state(state_code):
        return HighwayRoute.objects.filter(state=state_code, is_active=True)

    @staticmethod
    def seed_hpms_sources_from_csv(csv_path, source_dataset=None):
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"No existe el archivo HPMS maestro: {csv_path}")

        created_count = 0
        updated_count = 0

        with csv_path.open(mode="r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                state_name = _normalize_name(row.get("State"))
                api_url = _normalize_name(row.get("API URL"))
                map_url = _normalize_name(row.get("Map URL"))
                if not state_name or not api_url:
                    continue

                defaults = {
                    "state_code": _infer_state_code(state_name),
                    "api_url": api_url,
                    "map_url": map_url,
                    "source_dataset": source_dataset,
                    "is_active": True,
                }
                _, created = HPMSInventorySource.objects.update_or_create(
                    state_name=state_name,
                    defaults=defaults,
                )
                created_count += int(created)
                updated_count += int(not created)

        return {
            "created": created_count,
            "updated": updated_count,
            "total_sources": HPMSInventorySource.objects.count(),
        }

    @staticmethod
    def discover_hpms_schema(source: HPMSInventorySource, timeout: int = 30):
        try:
            response = requests.get(source.api_url, params={"f": "json"}, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # pragma: no cover - depends on remote endpoint
            source.last_error = str(exc)
            source.last_discovered_at = timezone.now()
            source.save(update_fields=["last_error", "last_discovered_at"])
            return {"source": source.state_name, "discovered_layers": 0, "error": str(exc)}

        if "error" in payload:
            message = payload["error"].get("message", "Error desconocido")
            source.last_error = message
            source.last_discovered_at = timezone.now()
            source.metadata = payload
            source.save(update_fields=["last_error", "last_discovered_at", "metadata"])
            return {"source": source.state_name, "discovered_layers": 0, "error": message}

        layers = payload.get("layers", [])
        tables = payload.get("tables", [])
        discovered_layers = 0

        for layer_meta in layers + tables:
            layer_id = layer_meta.get("id")
            if layer_id is None:
                continue

            layer, _ = HPMSLayerCatalog.objects.update_or_create(
                source=source,
                layer_id=layer_id,
                defaults={
                    "layer_name": layer_meta.get("name", f"Layer {layer_id}"),
                    "geometry_type": layer_meta.get("geometryType", ""),
                    "supports_query": "Query" in layer_meta.get("capabilities", ""),
                    "metadata": layer_meta,
                    "last_schema_sync": timezone.now(),
                },
            )
            discovered_layers += 1

            try:
                layer_response = requests.get(f"{source.api_url}/{layer_id}", params={"f": "json"}, timeout=timeout)
                layer_response.raise_for_status()
                layer_payload = layer_response.json()
            except Exception as exc:  # pragma: no cover - depends on remote endpoint
                layer.metadata = {**layer.metadata, "schema_error": str(exc)}
                layer.save(update_fields=["metadata"])
                continue

            fields = layer_payload.get("fields", [])
            layer.geometry_type = layer_payload.get("geometryType", layer.geometry_type)
            layer.supports_query = "Query" in layer_payload.get("capabilities", "")
            layer.record_count = layer_payload.get("maxRecordCount") or layer.record_count
            layer.metadata = layer_payload
            layer.last_schema_sync = timezone.now()
            layer.save()

            for field in fields:
                field_name = field.get("name", "")
                normalized_name = _normalize_token(field_name)
                HPMSFieldCatalog.objects.update_or_create(
                    layer=layer,
                    field_name=field_name,
                    defaults={
                        "field_alias": field.get("alias", ""),
                        "field_type": field.get("type", ""),
                        "is_nullable": field.get("nullable", True),
                        "is_candidate_iri": "iri" in normalized_name or "rough" in normalized_name,
                        "is_candidate_surface": "surface" in normalized_name or "pavement" in normalized_name,
                        "is_candidate_aadt": "aadt" in normalized_name or "traffic" in normalized_name,
                        "metadata": field,
                    },
                )

        source.last_discovered_at = timezone.now()
        source.last_successful_sync = timezone.now()
        source.last_error = ""
        source.metadata = payload
        source.save(update_fields=["last_discovered_at", "last_successful_sync", "last_error", "metadata"])

        return {
            "source": source.state_name,
            "discovered_layers": discovered_layers,
            "discovered_fields": HPMSFieldCatalog.objects.filter(layer__source=source).count(),
        }

    @staticmethod
    def discover_all_hpms_sources(limit: int | None = None, states: list[str] | None = None):
        queryset = HPMSInventorySource.objects.filter(is_active=True)
        if states:
            queryset = queryset.filter(state_name__in=states)
        results = []
        for source in queryset.order_by("state_name")[:limit]:
            results.append(RouteService.discover_hpms_schema(source))
        return results

    @staticmethod
    @transaction.atomic
    def import_hpms_segments(rows, source=None, layer=None, default_state=None):
        created_count = 0
        updated_count = 0
        snapshot_count = 0

        rows = list(rows)
        if not rows:
            return {"created": 0, "updated": 0, "snapshots": 0}

        for row in rows:
            geometry = row.get("geometry") if isinstance(row.get("geometry"), dict) else None
            derived_lat, derived_lon = _extract_midpoint_from_geometry(geometry)

            record = {
                "external_segment_id": _pick_value(row, FIELD_HINTS["external_segment_id"]) or "",
                "source_record_id": _pick_value(row, FIELD_HINTS["source_record_id"]) or "",
                "state_name": _normalize_name(_pick_value(row, FIELD_HINTS["state_name"]) or default_state or (source.state_name if source else "")),
                "county_name": _normalize_name(_pick_value(row, FIELD_HINTS["county_name"]) or ""),
                "route_name": _normalize_name(_pick_value(row, FIELD_HINTS["route_name"]) or ""),
                "route_number": _normalize_name(_pick_value(row, FIELD_HINTS["route_number"]) or ""),
                "route_type": _normalize_name(_pick_value(row, FIELD_HINTS["route_type"]) or ""),
                "functional_class": _normalize_name(_pick_value(row, FIELD_HINTS["functional_class"]) or ""),
                "is_nhs": _to_bool(_pick_value(row, FIELD_HINTS["is_nhs"])),
                "is_interstate": _to_bool(_pick_value(row, FIELD_HINTS["is_interstate"])),
                "urban_code": _normalize_name(_pick_value(row, FIELD_HINTS["urban_code"]) or ""),
                "start_measure": _to_float(_pick_value(row, FIELD_HINTS["start_measure"])),
                "end_measure": _to_float(_pick_value(row, FIELD_HINTS["end_measure"])),
                "length_miles": _to_float(_pick_value(row, FIELD_HINTS["length_miles"])),
                "iri": _to_float(_pick_value(row, FIELD_HINTS["iri"])),
                "surface_type": _normalize_name(_pick_value(row, FIELD_HINTS["surface_type"]) or ""),
                "pavement_type": _normalize_name(_pick_value(row, FIELD_HINTS["pavement_type"]) or ""),
                "aadt": _to_int(_pick_value(row, FIELD_HINTS["aadt"])),
                "truck_aadt": _to_int(_pick_value(row, FIELD_HINTS["truck_aadt"])),
                "lane_count": _to_int(_pick_value(row, FIELD_HINTS["lane_count"])),
                "mid_latitude": _to_float(_pick_value(row, FIELD_HINTS["mid_latitude"])) or derived_lat,
                "mid_longitude": _to_float(_pick_value(row, FIELD_HINTS["mid_longitude"])) or derived_lon,
                "year_recorded": _to_int(_pick_value(row, FIELD_HINTS["year_recorded"])),
                "geometry_json": geometry,
                "raw_attributes": row,
            }

            record["roughness_class"] = _classify_iri(record["iri"])
            record["data_quality_score"] = round(
                sum(
                    1
                    for field_name in ("route_number", "iri", "mid_latitude", "mid_longitude", "year_recorded")
                    if record.get(field_name) not in (None, "", {})
                )
                / 5
                * 100,
                2,
            )
            segment_hash_input = "|".join(
                [
                    record["state_name"],
                    record["route_number"],
                    str(record["start_measure"] or ""),
                    str(record["end_measure"] or ""),
                    record["external_segment_id"],
                ]
            )
            segment_key = hashlib.sha1(segment_hash_input.encode("utf-8")).hexdigest()[:20]

            defaults = {
                **record,
                "source": source,
                "layer": layer,
                "last_seen_at": timezone.now(),
            }
            _, created = HPMSRoadSegment.objects.update_or_create(segment_key=segment_key, defaults=defaults)
            created_count += int(created)
            updated_count += int(not created)

            segment = HPMSRoadSegment.objects.get(segment_key=segment_key)
            year = record["year_recorded"] or timezone.now().year
            HPMSConditionSnapshot.objects.update_or_create(
                segment=segment,
                year=year,
                defaults={
                    "iri": record["iri"],
                    "roughness_class": record["roughness_class"],
                    "surface_type": record["surface_type"],
                    "pavement_type": record["pavement_type"],
                    "aadt": record["aadt"],
                    "truck_aadt": record["truck_aadt"],
                    "lane_count": record["lane_count"],
                    "condition_score": _condition_score_from_iri(record["iri"]),
                    "data_quality_score": record["data_quality_score"],
                    "measured_at": timezone.now(),
                },
            )
            snapshot_count += 1

        return {"created": created_count, "updated": updated_count, "snapshots": snapshot_count}

    @staticmethod
    def match_segments_to_routes(state_code: str | None = None):
        routes = HighwayRoute.objects.filter(is_active=True)
        if state_code:
            routes = routes.filter(state__iexact=state_code)

        created_count = 0
        for route in routes:
            route_name_token = _normalize_token(route.route_name)
            route_id_token = _normalize_token(route.route_id)
            candidates = HPMSRoadSegment.objects.filter(
                Q(state_name__iexact=route.state) | Q(source__state_code__iexact=route.state)
            )
            if route_id_token:
                candidates = candidates.filter(
                    Q(route_number__icontains=route.route_id) | Q(route_name__icontains=route.route_name)
                )

            primary_segment = candidates.order_by("-is_interstate", "-is_nhs", "iri").first()
            if not primary_segment and route_name_token:
                primary_segment = HPMSRoadSegment.objects.filter(route_name__icontains=route.route_name).order_by("-is_nhs", "iri").first()
            if not primary_segment:
                continue

            match, created = RouteSegmentMatch.objects.update_or_create(
                highway_route=route,
                hpms_segment=primary_segment,
                defaults={
                    "match_method": "route_name_route_number",
                    "overlap_ratio": 1.0 if primary_segment.route_number else 0.6,
                    "is_primary_match": True,
                },
            )
            if created:
                created_count += 1

            RouteSegmentMatch.objects.filter(highway_route=route).exclude(pk=match.pk).update(is_primary_match=False)

        return {"matched_routes": created_count, "total_matches": RouteSegmentMatch.objects.count()}

    @staticmethod
    def get_adjustment_for_position(latitude, longitude):
        lat = _to_float(latitude)
        lon = _to_float(longitude)
        if lat is None or lon is None:
            return 0.0

        candidates = HPMSRoadSegment.objects.filter(
            mid_latitude__isnull=False,
            mid_longitude__isnull=False,
            mid_latitude__gte=lat - 1.0,
            mid_latitude__lte=lat + 1.0,
            mid_longitude__gte=lon - 1.0,
            mid_longitude__lte=lon + 1.0,
        )[:500]

        nearest = None
        nearest_distance = None
        for segment in candidates:
            distance = math.sqrt((segment.mid_latitude - lat) ** 2 + (segment.mid_longitude - lon) ** 2)
            if nearest_distance is None or distance < nearest_distance:
                nearest = segment
                nearest_distance = distance

        if not nearest:
            return 0.0
        return _route_adjustment_from_iri(nearest.iri)

    @staticmethod
    def summarize_hpms():
        total_segments = HPMSRoadSegment.objects.count()
        return {
            "total_sources": HPMSInventorySource.objects.count(),
            "discovered_layers": HPMSLayerCatalog.objects.count(),
            "segments_loaded": total_segments,
            "segments_with_iri": HPMSRoadSegment.objects.filter(iri__isnull=False).count(),
            "matched_routes": RouteSegmentMatch.objects.count(),
        }
