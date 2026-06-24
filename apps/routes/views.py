from __future__ import annotations

import hashlib
import heapq
from pathlib import Path

from django.conf import settings
from django.db.models import Avg, Count
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import _extract_latlon_points, _iter_geojson_features
from apps.data_ingestion.models import DataSource

from .models import HPMSInventorySource, HPMSRoadSegment
from .serializers import HPMSInventorySourceSerializer, HPMSRoadSegmentSerializer
from .services import RouteService, _classify_iri

_SYNTHETIC_NHS_CACHE = {
    "cache_key": None,
    "features": None,
}


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _severity_from_iri(iri_value):
    if iri_value is None:
        return 0.0
    return round(_clamp((float(iri_value) - 70.0) / 170.0, 0.0, 1.0), 3)


def _risk_label_from_iri(iri_value):
    if iri_value is None:
        return "Sin dato"
    if iri_value < 95:
        return "Baja rugosidad"
    if iri_value < 170:
        return "Rugosidad moderada"
    if iri_value < 220:
        return "Riesgo alto"
    return "Riesgo critico"


def _normalize_line_geometry(geometry):
    if not isinstance(geometry, dict):
        return None
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geom_type not in {"LineString", "MultiLineString"}:
        return None
    if not isinstance(coordinates, list) or not coordinates:
        return None
    return {
        "type": geom_type,
        "coordinates": coordinates,
    }


def _segment_feature(segment):
    geometry = _normalize_line_geometry(segment.geometry_json)
    if not geometry or segment.iri is None:
        return None

    iri_value = round(float(segment.iri), 1)
    roughness_class = segment.roughness_class or _classify_iri(segment.iri) or "UNKNOWN"
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "segment_key": segment.segment_key,
            "route_name": segment.route_name or segment.route_number or "Ruta HPMS",
            "route_number": segment.route_number or "",
            "state_name": segment.state_name or "",
            "county_name": segment.county_name or "",
            "length_miles": round(float(segment.length_miles), 2) if segment.length_miles is not None else None,
            "iri": iri_value,
            "roughness_class": roughness_class,
            "risk_label": _risk_label_from_iri(segment.iri),
            "severity": _severity_from_iri(segment.iri),
            "is_synthetic": False,
            "source_type": "hpms",
        },
    }


def _downsample_latlon_points(points, max_points=36):
    if len(points) <= max_points:
        return points
    step = max(1, int(len(points) / max_points))
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


def _resolve_nhs_geojson_path():
    preferred_files = [
        settings.MEDIA_ROOT / "datasets" / "routes_colored_simplified.geojson",
        settings.MEDIA_ROOT / "datasets" / "routes_simplified.geojson",
        settings.MEDIA_ROOT / "datasets" / "routes_interstate_simplified.geojson",
    ]
    for route_file in preferred_files:
        if route_file.exists():
            return route_file

    dataset = DataSource.objects.filter(file_type="GEOJSON").order_by("-last_load").first()
    if dataset and dataset.file_path:
        dataset_path = Path(dataset.file_path)
        if dataset_path.exists():
            return dataset_path
    return None


def _is_continental_us(points):
    if not points:
        return False
    lat, lon = points[len(points) // 2]
    return 24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0


def _build_synthetic_feature(route, coords, segment_index, source_type="synthetic_nhs"):
    if len(coords) < 2:
        return None

    hash_input = f"{route['id']}:{segment_index}".encode("utf-8")
    seed = int(hashlib.sha1(hash_input).hexdigest()[:8], 16)
    route_bias = (seed % 31) - 15
    iri_value = round(85 + ((seed % 1000) / 999) * 145 + route_bias, 1)
    iri_value = round(_clamp(iri_value, 75.0, 245.0), 1)
    roughness_class = _classify_iri(iri_value) or "UNKNOWN"

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in coords],
        },
        "properties": {
            "segment_key": f"{route['id']}-roughness-{segment_index}",
            "route_name": route.get("name") or route.get("id") or "Ruta demo",
            "route_number": route.get("id") or "",
            "state_name": "Demo",
            "county_name": "",
            "length_miles": None,
            "iri": iri_value,
            "roughness_class": roughness_class,
            "risk_label": _risk_label_from_iri(iri_value),
            "severity": _severity_from_iri(iri_value),
            "is_synthetic": True,
            "source_type": source_type,
        },
    }


def _synthetic_roughness_features(max_features):
    geojson_path = _resolve_nhs_geojson_path()
    if not geojson_path:
        return []

    cache_key = f"{geojson_path}:{Path(geojson_path).stat().st_mtime}"
    cached_features = _SYNTHETIC_NHS_CACHE.get("features") or []
    if _SYNTHETIC_NHS_CACHE.get("cache_key") == cache_key and len(cached_features) >= max_features:
        return cached_features[:max_features]

    reservoir = []
    candidate_count = 0

    for feature_index, feature in enumerate(_iter_geojson_features(str(geojson_path)), start=1):
        geometry = feature.get("geometry") or {}
        coords = _extract_latlon_points(geometry)
        if len(coords) < 2 or not _is_continental_us(coords):
            continue

        props = feature.get("properties") or {}
        route_name = (
            str(props.get("n") or "").strip()
            or str(props.get("LNAME") or "").strip()
            or str(props.get("ROUTEID") or "").strip()
            or f"Corredor NHS {feature_index}"
        )
        route_type = str(props.get("t") or props.get("route_type") or "").strip()
        route_id = str(props.get("ROUTEID") or props.get("routeid") or route_name or feature_index).strip()
        route_key = f"{route_type}:{route_id}:{feature_index}"

        sampled_coords = _downsample_latlon_points(coords, max_points=24)
        if len(sampled_coords) < 2:
            continue

        synthetic_feature = _build_synthetic_feature(
            {"id": route_key, "name": route_name},
            sampled_coords,
            feature_index,
            source_type="synthetic_nhs",
        )
        if not synthetic_feature:
            continue

        score_key = f"{route_key}:{sampled_coords[0]}:{sampled_coords[-1]}".encode("utf-8")
        score = int(hashlib.sha1(score_key).hexdigest()[:12], 16)
        heap_item = (-score, candidate_count, synthetic_feature)
        candidate_count += 1

        if len(reservoir) < max_features:
            heapq.heappush(reservoir, heap_item)
            continue

        worst_score = -reservoir[0][0]
        if score < worst_score:
            heapq.heapreplace(reservoir, heap_item)

    ordered = sorted([(-score, idx, feat) for score, idx, feat in reservoir], key=lambda item: (item[0], item[1]))
    features = [feature for _, _, feature in ordered]
    _SYNTHETIC_NHS_CACHE["cache_key"] = cache_key
    _SYNTHETIC_NHS_CACHE["features"] = features
    return features[:max_features]


class HPMSSummaryAPIView(APIView):
    def get(self, request):
        summary = RouteService.summarize_hpms()
        by_state = list(
            HPMSRoadSegment.objects.values("state_name")
            .annotate(
                segments=Count("id"),
                avg_iri=Avg("iri"),
            )
            .order_by("state_name")[:20]
        )
        summary["by_state"] = by_state
        return Response(summary)


class HPMSSourceListAPIView(APIView):
    def get(self, request):
        queryset = HPMSInventorySource.objects.filter(is_active=True).order_by("state_name")
        serializer = HPMSInventorySourceSerializer(queryset, many=True)
        return Response(serializer.data)


class HPMSSegmentListAPIView(APIView):
    def get(self, request):
        queryset = HPMSRoadSegment.objects.all().order_by("state_name", "route_number", "segment_key")
        state = request.GET.get("state")
        roughness = request.GET.get("roughness")
        nhs_only = request.GET.get("nhs")

        if state:
            queryset = queryset.filter(state_name__iexact=state)
        if roughness:
            queryset = queryset.filter(roughness_class__iexact=roughness)
        if nhs_only and nhs_only.lower() in {"1", "true", "yes", "si"}:
            queryset = queryset.filter(is_nhs=True)

        serializer = HPMSRoadSegmentSerializer(queryset[:200], many=True)
        return Response(serializer.data)


class HPMSSRoughnessGeoJSONAPIView(APIView):
    def get(self, request):
        state = request.GET.get("state")
        nhs_only = request.GET.get("nhs", "1")
        fallback = request.GET.get("fallback", "1")
        try:
            requested_limit = int(request.GET.get("limit", 260))
        except (TypeError, ValueError):
            requested_limit = 260
        max_features = _clamp(requested_limit, 50, 1200)

        queryset = HPMSRoadSegment.objects.filter(iri__isnull=False).exclude(geometry_json__isnull=True)
        if state:
            queryset = queryset.filter(state_name__iexact=state)
        if str(nhs_only).lower() in {"1", "true", "yes", "si"}:
            queryset = queryset.filter(is_nhs=True)

        features = []
        for segment in queryset.order_by("-iri", "state_name", "route_number")[:max_features]:
            feature = _segment_feature(segment)
            if feature:
                features.append(feature)

        using_real_hpms = bool(features)
        fallback_allowed = str(fallback).lower() not in {"0", "false", "no"}
        if not features and fallback_allowed:
            features = _synthetic_roughness_features(max_features=max_features)

        return JsonResponse(
            {
                "type": "FeatureCollection",
                "features": features,
                "meta": {
                    "feature_count": len(features),
                    "using_real_hpms": using_real_hpms,
                    "using_fallback": bool(features) and not using_real_hpms,
                    "source": "hpms" if using_real_hpms else "synthetic_nhs_routes",
                },
            }
        )
