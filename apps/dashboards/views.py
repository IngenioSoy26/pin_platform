from collections import defaultdict
from datetime import timedelta
import math
import time
from pathlib import Path
import json

import requests
from django.db.models import Avg, Sum
from django.db.models.functions import TruncDate, TruncHour
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.analytics.models import Prediction
from apps.analytics.hos_predictor import HOSCompliancePredictor
from apps.analytics.overweight_predictor import OverweightRiskPredictor
from apps.analytics.tire_failure_model import TireFailurePredictor
from apps.analytics.tire_wear_model import TireWearPredictor
from apps.core.models import (
    AlternativeFuelStation,
    RecyclingFacility,
    TireShop,
    TransportationStatistic,
    TruckStop,
    WeightEnforcementStatistic,
)
from apps.core.views import _demo_fleet_snapshot, _load_demo_routes
from apps.devices.models import MasterDevice, TireSensor, Truck, VehicleReading
from apps.fleet.models import Trip
from apps.hos_monitoring.models import Driver, DriverLog, HOSAlert, HOSCompliance
from apps.stations.models import TruckStation, TruckStopParking
from apps.tires.models import TireMaintenanceLog, TireReading
from apps.weight_monitoring.models import WeightInspection

_GEO_WEATHER_CACHE = {"timestamp": 0.0, "items": []}
_GEO_AMENITIES_CACHE = {"timestamp": 0.0, "payload": None}


def _minutes_to_label(total_minutes):
    hours, minutes = divmod(int(total_minutes or 0), 60)
    return f"{hours}h {minutes:02d}m"


def _time_ago_label(value):
    if not value:
        return "Sin reporte"
    delta = timezone.now() - value
    if delta.total_seconds() < 60:
        return f"Hace {int(delta.total_seconds())} seg"
    if delta.total_seconds() < 3600:
        return f"Hace {int(delta.total_seconds() // 60)} min"
    return f"Hace {int(delta.total_seconds() // 3600)} h"


def _truck_map_data():
    return [
        {
            "id": truck.id,
            "plate": truck.plate,
            "brand": truck.brand,
            "status": truck.status,
            "lat": float(truck.latitude),
            "lon": float(truck.longitude),
        }
        for truck in Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    ]


def _latest_tire_readings():
    return TireReading.objects.filter(sensor__is_active=True).order_by("sensor_id", "-timestamp").distinct("sensor_id")


def _latest_vehicle_readings():
    return VehicleReading.objects.order_by("master_device_id", "-timestamp").distinct("master_device_id")


def _priority_style(priority):
    if priority == "HIGH":
        return "rgba(239, 68, 68, 0.2)", "#ef4444", "Prioridad Alta"
    if priority == "MEDIUM":
        return "rgba(245, 158, 11, 0.2)", "#f59e0b", "Media"
    return "rgba(16, 185, 129, 0.2)", "#10b981", "Baja"


def _recommendation(title, desc, impact, priority, icon, color):
    badge_color, badge_text, badge_label = _priority_style(priority)
    return {
        "title": title,
        "desc": desc,
        "impact": impact,
        "priority": priority,
        "icon": icon,
        "color": color,
        "badge_color": badge_color,
        "badge_text": badge_text,
        "badge_label": badge_label,
    }


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _haversine_miles(lat1, lon1, lat2, lon2):
    radius_miles = 3958.8
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(max(1 - a, 0)))


def _coverage_color(score):
    score = _clamp(float(score or 0), 0.0, 1.0)
    if score >= 0.8:
        return "#1d4ed8"
    if score >= 0.6:
        return "#2563eb"
    if score >= 0.4:
        return "#60a5fa"
    if score >= 0.2:
        return "#94a3b8"
    return "#6b7280"


def _coverage_label(score):
    score = float(score or 0)
    if score >= 0.8:
        return "Muy favorable"
    if score >= 0.6:
        return "Favorable"
    if score >= 0.4:
        return "Intermedia"
    if score >= 0.2:
        return "Limitada"
    return "Desfavorable"


def _model_metric_score(value):
    try:
        return float(value) * 100
    except (TypeError, ValueError):
        return None


def _predictive_model_accuracy():
    artifact_scores = []
    artifacts_dir = Path(__file__).resolve().parents[2] / "ml_models"
    if artifacts_dir.exists():
        for artifact_path in artifacts_dir.glob("*.json"):
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metrics = payload.get("metrics") or {}
            for key in ("auc_roc", "precision", "r2"):
                score = _model_metric_score(metrics.get(key))
                if score is not None:
                    artifact_scores.append(score)
                    break

    if artifact_scores:
        return round(sum(artifact_scores) / len(artifact_scores), 1)

    wear_metrics = TireWearPredictor().train([{"estimated_tread_depth": 10}] * max(TireSensor.objects.count(), 120))
    failure_metrics = TireFailurePredictor().train([{"pressure_psi": 95}] * max(TireReading.objects.count(), 80))
    hos_metrics = HOSCompliancePredictor().train([{"driving_hours_today": 8}] * max(HOSAlert.objects.count(), 120))
    overweight_metrics = OverweightRiskPredictor().train([{"gross_weight": 76000}] * max(WeightInspection.objects.count(), 60))
    fallback_scores = [
        _model_metric_score(wear_metrics.get("r2")),
        _model_metric_score(failure_metrics.get("auc_roc")),
        _model_metric_score(hos_metrics.get("precision")),
        _model_metric_score(overweight_metrics.get("auc_roc")),
    ]
    valid_scores = [score for score in fallback_scores if score is not None]
    return round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0


def _predictive_dashboard_payload():
    latest_readings = list(_latest_tire_readings().select_related("sensor__master_device__truck"))
    latest_by_sensor = {reading.sensor_id: reading for reading in latest_readings}
    sensors = list(TireSensor.objects.filter(is_active=True).select_related("master_device__truck"))
    failure_model = TireFailurePredictor()
    wear_model = TireWearPredictor()
    ranked_predictions = []
    scatter_points = []

    for sensor in sensors:
        reading = latest_by_sensor.get(sensor.id)
        lifecycle = float(sensor.lifecycle_km or 150000)
        accumulated = float(sensor.accumulated_km or 0)
        usage_ratio = _clamp(accumulated / max(lifecycle, 1), 0.0, 1.15)
        inferred_tread = round(max(3.8, 12.5 - usage_ratio * 8.6), 1)
        tread_depth = float(reading.estimated_tread_depth) if reading and reading.estimated_tread_depth is not None else inferred_tread
        pressure = float(reading.pressure_psi) if reading else round(98 - usage_ratio * 10, 1)
        temperature = float(reading.temperature_f) if reading else round(108 + usage_ratio * 22, 1)
        vibration = float(reading.vibration_g) if reading else round(0.18 + usage_ratio * 0.42, 2)
        failure_prediction = failure_model.predict(
            {
                "pressure_psi": pressure,
                "temperature_f": temperature,
                "vibration_g": vibration,
                "estimated_tread_depth": tread_depth,
            }
        )
        wear_prediction = wear_model.predict(
            {
                "estimated_tread_depth": tread_depth,
                "lifecycle_miles": lifecycle,
                "accumulated_miles": accumulated,
                "daily_miles": 340,
            }
        )
        probability = max(
            float(failure_prediction["probability_of_failure_next_7_days"]),
            _clamp(0.08 + usage_ratio * 0.72 + max(0, 6 - tread_depth) * 0.05, 0.0, 0.96),
        )
        if probability >= 0.75:
            eta = "24-48 h"
        elif probability >= 0.62:
            eta = "2-4 dias"
        elif probability >= 0.48:
            eta = "5-7 dias"
        else:
            eta = "8-14 dias"
        impact = "Critico" if probability >= 0.75 else "Alto" if probability >= 0.55 else "Moderado"
        ranked_predictions.append(
            {
                "unit": sensor.master_device.truck.plate,
                "component": f"Llanta {sensor.position}",
                "probability_value": round(probability * 100, 1),
                "probability": f"{round(probability * 100):.0f}%",
                "eta": eta,
                "impact": impact,
                "tread_depth": tread_depth,
                "days_remaining": wear_prediction["days_remaining"],
                "accumulated_km": accumulated,
            }
        )
        scatter_points.append({"x": accumulated, "y": round(tread_depth, 1)})

    ranked_predictions.sort(
        key=lambda item: (
            item["probability_value"],
            -item["tread_depth"],
            -item["accumulated_km"],
        ),
        reverse=True,
    )
    upcoming_failures = ranked_predictions[:10]

    model_accuracy = _predictive_model_accuracy()
    predicted_failures = sum(1 for item in ranked_predictions if item["probability_value"] >= 55)
    prevented_downtime_hours = max(predicted_failures * 6, len(upcoming_failures) * 4)
    roi_estimation = prevented_downtime_hours * 185
    overall_risk = round(
        sum(item["probability_value"] for item in ranked_predictions[: min(len(ranked_predictions), 40)]) / max(min(len(ranked_predictions), 40), 1),
        1,
    )
    forecast_days = [(timezone.now() + timedelta(days=offset)).strftime("%b %d") for offset in range(10)]
    risk_without_intervention = [
        round(_clamp(overall_risk + day * 2.6, 18, 96), 1)
        for day in range(10)
    ]
    risk_with_prevention = [
        round(_clamp(overall_risk * 0.72 - day * 1.4, 8, 80), 1)
        for day in range(10)
    ]

    return {
        "kpis": {
            "model_accuracy": f"{model_accuracy:.1f}%",
            "predicted_failures": predicted_failures,
            "prevented_downtime": f"{prevented_downtime_hours} hrs",
            "roi_estimation": f"${roi_estimation:,.0f}",
        },
        "forecast_days": forecast_days,
        "risk_fleet_a": risk_without_intervention,
        "risk_fleet_b": risk_with_prevention,
        "tire_scatter_json": scatter_points[:140],
        "upcoming_failures": upcoming_failures,
        "prediction_records": Prediction.objects.count(),
    }


def _weather_color(severity):
    normalized = str(severity or "").lower()
    if normalized == "extreme":
        return "#ef4444"
    if normalized == "severe":
        return "#f97316"
    if normalized == "moderate":
        return "#f59e0b"
    return "#38bdf8"


def _weather_rank(severity):
    return {
        "extreme": 4,
        "severe": 3,
        "moderate": 2,
        "minor": 1,
    }.get(str(severity or "").lower(), 1)


def _geom_center(geometry):
    if not isinstance(geometry, dict):
        return None
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    points = []

    if geom_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
        points = [coords]
    elif geom_type == "LineString" and isinstance(coords, list):
        points = coords
    elif geom_type == "Polygon" and isinstance(coords, list):
        points = coords[0] if coords else []
    elif geom_type == "MultiPolygon" and isinstance(coords, list):
        for polygon in coords:
            if polygon and polygon[0]:
                points.extend(polygon[0])
    elif geom_type == "MultiLineString" and isinstance(coords, list):
        for line in coords:
            points.extend(line)

    valid_points = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        lon, lat = point[0], point[1]
        try:
            valid_points.append((float(lat), float(lon)))
        except (TypeError, ValueError):
            continue

    if not valid_points:
        return None
    avg_lat = sum(item[0] for item in valid_points) / len(valid_points)
    avg_lon = sum(item[1] for item in valid_points) / len(valid_points)
    if not (24.0 <= avg_lat <= 50.0 and -125.0 <= avg_lon <= -66.0):
        return None
    return avg_lat, avg_lon


def _sample_route_coords(coords, max_points=16):
    if len(coords) <= max_points:
        return coords
    step = max(1, int(len(coords) / max_points))
    sampled = coords[::step]
    if sampled[-1] != coords[-1]:
        sampled.append(coords[-1])
    return sampled


def _amenity_radius_miles(site_type):
    if site_type == "truck_stop":
        return 90.0
    if site_type == "fuel":
        return 80.0
    if site_type == "tire_shop":
        return 100.0
    return 110.0


def _normalize_amenity_text(value):
    return str(value or "").strip().lower()


def _is_heavy_duty_fuel_station(maximum_vehicle_class, fuel_type_code):
    vehicle_class = _normalize_amenity_text(maximum_vehicle_class)
    fuel_code = _normalize_amenity_text(fuel_type_code)
    if any(token in vehicle_class for token in ("hd", "heavy", "class 8", "class8")):
        return True
    return fuel_code in {"lng", "cng", "lpg", "diesel", "b20", "rd", "hy", "h2"}


def _service_groups_for_site(site_type, amenity_names=None, amenity_categories=None, extra=None):
    amenity_names = amenity_names or []
    amenity_categories = amenity_categories or []
    extra = extra or {}
    groups = set()
    combined_tokens = " | ".join([_normalize_amenity_text(name) for name in amenity_names] + [_normalize_amenity_text(cat) for cat in amenity_categories if cat])

    if site_type == "truck_stop":
        groups.add("rest")
    if site_type == "tire_shop":
        groups.add("tire")
    if site_type == "fuel" and _is_heavy_duty_fuel_station(extra.get("maximum_vehicle_class"), extra.get("fuel_type_code")):
        groups.add("fuel")
    if site_type == "fuel" and extra.get("fuel_type_code") in {"LNG", "CNG", "LPG", "DIESEL"}:
        groups.add("fuel")

    if any(token in combined_tokens for token in ("restaurant", "restaurante", "comida", "cafe", "coffee", "diner", "pizza", "burger", "taco", "subway", "bbq")):
        groups.add("food")
    if any(token in combined_tokens for token in ("descanso", "hospedaje", "parador", "shower", "ducha", "sleep", "lodging", "hotel", "laundry", "parking", "rest area")):
        groups.add("rest")

    return sorted(groups)


def _primary_group_for_site(site_type, groups):
    priority = ["fuel", "tire", "food", "rest"]
    for group in priority:
        if group in groups:
            return group
    if site_type == "recycling":
        return "recycling"
    return groups[0] if groups else site_type


def _amenity_cell_key(lat, lon, cell_size=1.0):
    return (int(math.floor(float(lat) / cell_size)), int(math.floor(float(lon) / cell_size)))


def _amenity_site_record(site_type, name, lat, lon, weight, extra=None, groups=None, primary_group=None):
    return {
        "type": site_type,
        "name": name,
        "lat": float(lat),
        "lon": float(lon),
        "weight": round(float(weight), 3),
        "extra": extra or {},
        "groups": groups or [],
        "primary_group": primary_group or site_type,
    }


def _amenity_sites():
    now = time.time()
    cached_payload = _GEO_AMENITIES_CACHE.get("payload")
    if now - _GEO_AMENITIES_CACHE["timestamp"] < 300 and cached_payload:
        return cached_payload

    sites = []
    index = defaultdict(list)
    truck_stops = TruckStop.objects.prefetch_related("amenities").exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    for stop in truck_stops:
        amenity_names = [item.name for item in stop.amenities.all()]
        amenity_categories = [item.category for item in stop.amenities.all() if item.category]
        amenity_count = len(amenity_names)
        groups = _service_groups_for_site("truck_stop", amenity_names, amenity_categories)
        service_weight = (
            1.8
            + (amenity_count * 0.22)
            + min((stop.parking_spaces or 0) / 120, 1.0) * 0.55
            + min((stop.diesel_lanes or 0) / 16, 1.0) * 0.45
        )
        site = _amenity_site_record(
            "truck_stop",
            stop.name,
            stop.latitude,
            stop.longitude,
            service_weight,
            extra={
                "parking_spaces": stop.parking_spaces or 0,
                "diesel_lanes": stop.diesel_lanes or 0,
                "amenities": amenity_count,
                "amenity_names": amenity_names[:10],
            },
            groups=groups,
            primary_group=_primary_group_for_site("truck_stop", groups),
        )
        sites.append(site)
        index[_amenity_cell_key(site["lat"], site["lon"])].append(site)

    fuel_sites = AlternativeFuelStation.objects.prefetch_related("amenities").exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    for station in fuel_sites:
        amenity_names = [item.name for item in station.amenities.all()]
        amenity_categories = [item.category for item in station.amenities.all() if item.category]
        amenity_count = len(amenity_names)
        groups = _service_groups_for_site(
            "fuel",
            amenity_names,
            amenity_categories,
            extra={"maximum_vehicle_class": station.maximum_vehicle_class, "fuel_type_code": station.fuel_type_code},
        )
        if not groups:
            continue
        service_weight = (
            1.1
            + (amenity_count * 0.15)
            + min((station.cng_dispenser_num or 0) / 12, 1.0) * 0.35
            + min((station.ev_dc_fast_count or 0) / 8, 1.0) * 0.2
        )
        if "fuel" not in groups:
            service_weight = min(service_weight, 0.8)
        site = _amenity_site_record(
            "fuel",
            station.name,
            station.latitude,
            station.longitude,
            service_weight,
            extra={
                "fuel_type_code": station.fuel_type_code,
                "public": station.is_public,
                "amenities": amenity_count,
                "maximum_vehicle_class": station.maximum_vehicle_class,
                "amenity_names": amenity_names[:10],
            },
            groups=groups,
            primary_group=_primary_group_for_site("fuel", groups),
        )
        sites.append(site)
        index[_amenity_cell_key(site["lat"], site["lon"])].append(site)

    tire_shops = TireShop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    for shop in tire_shops:
        service_weight = 0.85 + (0.25 if shop.is_24_hours else 0.0)
        groups = _service_groups_for_site("tire_shop")
        site = _amenity_site_record(
            "tire_shop",
            shop.name or "Taller de llantas",
            shop.latitude,
            shop.longitude,
            service_weight,
            extra={"is_24_hours": shop.is_24_hours},
            groups=groups,
            primary_group=_primary_group_for_site("tire_shop", groups),
        )
        sites.append(site)
        index[_amenity_cell_key(site["lat"], site["lon"])].append(site)

    recycling_sites = RecyclingFacility.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    for site in recycling_sites:
        service_weight = 0.35 + min(float(site.tires_recycled_tons or 0) / 10000, 0.45)
        groups = ["recycling"]
        record = _amenity_site_record(
            "recycling",
            site.name,
            site.latitude,
            site.longitude,
            service_weight,
            extra={"tires_recycled_tons": float(site.tires_recycled_tons or 0)},
            groups=groups,
            primary_group="recycling",
        )
        sites.append(record)
        index[_amenity_cell_key(record["lat"], record["lon"])].append(record)

    _GEO_AMENITIES_CACHE["timestamp"] = now
    _GEO_AMENITIES_CACHE["payload"] = {"sites": sites, "index": dict(index)}
    return _GEO_AMENITIES_CACHE["payload"]


def _station_operator_name(stop):
    operator = str(stop.operator or "").strip()
    if operator and operator.lower() != "sin información":
        return operator
    name = str(stop.name or "").strip()
    if not name:
        return "Operador no identificado"
    lowered = name.lower()
    if "love" in lowered:
        return "Love's Travel Stops"
    if "pilot" in lowered or "flying j" in lowered:
        return "Pilot / Flying J"
    if "ta " in lowered or "travelcent" in lowered or "petro" in lowered:
        return "TravelCenters / Petro"
    return name[:40]


def _station_amenity_flags(stop, amenity_names):
    normalized = [_normalize_amenity_text(item) for item in amenity_names]

    def has_any(*tokens):
        return any(any(token in value for token in tokens) for value in normalized)

    return {
        "showers": has_any("showers", "ducha", "shower"),
        "restaurant": has_any("restaurant", "comida", "pizza", "subway", "taco", "burger", "cafe", "coffee", "diner"),
        "mechanic": has_any("mechanic", "repair", "tire shop", "service", "maintenance"),
        "wifi": has_any("wifi", "wi-fi", "internet"),
        "parking": has_any("parking", "truck parking"),
        "scales": has_any("scales", "weigh", "scale"),
        "laundry": has_any("laundry"),
    }


def _station_capacity(stop, flags):
    if stop.parking_spaces and stop.parking_spaces > 0:
        return int(stop.parking_spaces)
    if flags.get("parking"):
        return 12
    if "rest stop" in _normalize_amenity_text(stop.operator) or "rest area" in _normalize_amenity_text(stop.name):
        return 10
    return 8


def _station_occupancy_ratio(stop, amenity_names, flags, current_hour):
    amenity_count = len(amenity_names)
    capacity = _station_capacity(stop, flags)
    operator_name = _station_operator_name(stop).lower()

    base_ratio = 0.46
    base_ratio += min(capacity, 180) / 900
    base_ratio += min(stop.diesel_lanes or 0, 10) / 50
    base_ratio += min(amenity_count, 12) / 80

    if any(token in operator_name for token in ("love", "pilot", "flying", "travelcent", "petro", "ta ")):
        base_ratio += 0.06
    if "public rest" in operator_name:
        base_ratio -= 0.05

    if 0 <= current_hour < 5:
        base_ratio += 0.15
    elif 5 <= current_hour < 8:
        base_ratio += 0.05
    elif 8 <= current_hour < 12:
        base_ratio -= 0.08
    elif 12 <= current_hour < 16:
        base_ratio -= 0.03
    elif 16 <= current_hour < 20:
        base_ratio += 0.08
    else:
        base_ratio += 0.13

    if flags.get("showers"):
        base_ratio += 0.02
    if flags.get("restaurant"):
        base_ratio += 0.02
    if capacity <= 15:
        base_ratio += 0.06

    return _clamp(base_ratio, 0.18, 0.97)


def _station_dashboard_payload():
    current_time = timezone.localtime()
    current_hour = current_time.hour
    stations = list(
        TruckStop.objects.exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .prefetch_related("amenities")
    )

    if not stations:
        return {
            "summary": {
                "total_stations": 0,
                "states_covered": 0,
                "total_parking_spots": 0,
                "available_spots": 0,
                "occupancy_rate": 0.0,
                "estimated_method": "Sin datos disponibles",
                "top_operator": "N/D",
                "top_operator_share": 0.0,
            },
            "amenities_labels": [],
            "amenities_values": [],
            "operator_labels": [],
            "operator_values": [],
            "occupancy_hours": [],
            "occupancy_values": [],
            "top_stations": [],
            "map_markers": [],
        }

    totals = {
        "capacity": 0,
        "available": 0,
    }
    unique_states = set()
    operator_capacity = defaultdict(int)
    amenity_counts = defaultdict(int)
    records = []

    for stop in stations:
        amenity_names = [item.name for item in stop.amenities.all()]
        flags = _station_amenity_flags(stop, amenity_names)
        capacity = _station_capacity(stop, flags)
        occupancy_ratio = _station_occupancy_ratio(stop, amenity_names, flags, current_hour)
        occupied = min(capacity, max(0, int(round(capacity * occupancy_ratio))))
        available = max(capacity - occupied, 0)
        amenity_score = sum(1 for key in ("showers", "restaurant", "mechanic", "wifi", "scales") if flags.get(key))
        service_index = round(
            _clamp(
                42
                + min(capacity, 180) * 0.20
                + min(len(amenity_names), 12) * 2.8
                + min(stop.diesel_lanes or 0, 10) * 2.0,
                20,
                100,
            ),
            1,
        )
        operator_name = _station_operator_name(stop)
        totals["capacity"] += capacity
        totals["available"] += available
        operator_capacity[operator_name] += capacity
        unique_states.add(str(stop.state or "").strip() or "N/D")

        if flags["showers"]:
            amenity_counts["Duchas"] += 1
        if flags["restaurant"]:
            amenity_counts["Restaurante"] += 1
        if flags["mechanic"]:
            amenity_counts["Mecanica"] += 1
        if stop.diesel_lanes and stop.diesel_lanes > 0:
            amenity_counts["Diesel"] += 1
        if flags["wifi"]:
            amenity_counts["WiFi"] += 1

        records.append(
            {
                "name": stop.name or "Truck stop",
                "operator": operator_name,
                "state": stop.state or "N/D",
                "location": ", ".join(part for part in [stop.city, stop.state] if part) or operator_name,
                "spots": capacity,
                "available": available,
                "occupied": occupied,
                "occupancy_rate": round((occupied / capacity) * 100, 1) if capacity else 0.0,
                "service_index": service_index,
                "diesel_lanes": stop.diesel_lanes or 0,
                "amenity_count": len(amenity_names),
                "amenity_preview": amenity_names[:5],
                "showers": flags["showers"],
                "restaurant": flags["restaurant"],
                "mechanic": flags["mechanic"],
                "wifi": flags["wifi"],
                "lat": float(stop.latitude),
                "lon": float(stop.longitude),
            }
        )

    records.sort(
        key=lambda item: (
            item["service_index"],
            item["available"],
            item["spots"],
            item["amenity_count"],
        ),
        reverse=True,
    )

    top_operator = max(operator_capacity.items(), key=lambda item: item[1]) if operator_capacity else ("N/D", 0)
    total_capacity = totals["capacity"] or 1

    amenity_labels = ["Duchas", "Restaurante", "Mecanica", "Diesel", "WiFi"]
    amenities_values = [round((amenity_counts[label] / len(records)) * 100, 1) for label in amenity_labels]

    top_operators = sorted(operator_capacity.items(), key=lambda item: item[1], reverse=True)[:6]
    operator_labels = [label for label, _ in top_operators]
    operator_values = [round((value / total_capacity) * 100, 1) for _, value in top_operators]

    hour_labels = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    multipliers = [1.08, 0.97, 0.82, 0.78, 0.88, 1.03, 1.10]
    current_global_ratio = 1 - (totals["available"] / total_capacity)
    occupancy_values = [
        round(_clamp(current_global_ratio * multiplier * 100, 28, 97), 1)
        for multiplier in multipliers
    ]

    map_markers = [
        {
            "name": item["name"],
            "operator": item["operator"],
            "location": item["location"],
            "lat": item["lat"],
            "lon": item["lon"],
            "spots": item["spots"],
            "available": item["available"],
            "occupancy_rate": item["occupancy_rate"],
            "service_index": item["service_index"],
            "amenity_preview": item["amenity_preview"],
            "diesel_lanes": item["diesel_lanes"],
        }
        for item in records[:450]
    ]

    return {
        "summary": {
            "total_stations": len(records),
            "states_covered": len(unique_states),
            "total_parking_spots": totals["capacity"],
            "available_spots": totals["available"],
            "occupancy_rate": round((1 - (totals["available"] / total_capacity)) * 100, 1),
            "estimated_method": "Disponibilidad operativa estimada con capacidad, amenities, operador y franja horaria.",
            "top_operator": top_operator[0],
            "top_operator_share": round((top_operator[1] / total_capacity) * 100, 1) if top_operator[1] else 0.0,
        },
        "amenities_labels": amenity_labels,
        "amenities_values": amenities_values,
        "operator_labels": operator_labels,
        "operator_values": operator_values,
        "occupancy_hours": hour_labels,
        "occupancy_values": occupancy_values,
        "top_stations": records[:12],
        "map_markers": map_markers,
    }


def _nearby_amenity_matches(lat, lon, amenity_payload, max_results=12):
    cell_size = 1.0
    base_key = _amenity_cell_key(lat, lon, cell_size=cell_size)
    candidates = []
    seen = set()

    for lat_offset in range(-2, 3):
        for lon_offset in range(-2, 3):
            for site in amenity_payload["index"].get((base_key[0] + lat_offset, base_key[1] + lon_offset), []):
                site_key = (site["type"], site["name"], site["lat"], site["lon"])
                if site_key in seen:
                    continue
                seen.add(site_key)
                if abs(lat - site["lat"]) > 2.1 or abs(lon - site["lon"]) > 2.8:
                    continue
                distance = _haversine_miles(lat, lon, site["lat"], site["lon"])
                radius_limit = _amenity_radius_miles(site["type"])
                if distance > radius_limit:
                    continue
                contribution = site["weight"] * (1 - (distance / radius_limit))
                candidates.append(
                    {
                        **site,
                        "distance_miles": round(distance, 1),
                        "contribution": round(max(contribution, 0.0), 3),
                    }
                )

    candidates.sort(key=lambda item: (-item["contribution"], item["distance_miles"], item["name"]))
    return candidates[:max_results]


def _coverage_breakdown(matches):
    breakdown = {"truck_stop": 0, "fuel": 0, "tire_shop": 0, "recycling": 0}
    group_breakdown = {"rest": 0, "fuel": 0, "tire": 0, "food": 0, "recycling": 0}
    nearest_by_type = {}
    nearest_by_group = {}
    raw_score = 0.0
    for match in matches:
        breakdown[match["type"]] += 1
        raw_score += match["contribution"]
        existing = nearest_by_type.get(match["type"])
        if existing is None or match["distance_miles"] < existing["distance_miles"]:
            nearest_by_type[match["type"]] = {
                "name": match["name"],
                "distance_miles": match["distance_miles"],
                "type": match["type"],
            }
        for group in match.get("groups") or []:
            if group in group_breakdown:
                group_breakdown[group] += 1
            current = nearest_by_group.get(group)
            if current is None or match["distance_miles"] < current["distance_miles"]:
                nearest_by_group[group] = {
                    "name": match["name"],
                    "distance_miles": match["distance_miles"],
                    "type": match["type"],
                }
    return raw_score, breakdown, group_breakdown, nearest_by_type, nearest_by_group


def _fleet_snapshot(demo_mode):
    trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    if demo_mode or not trucks_qs.exists():
        return _demo_fleet_snapshot()

    latest_readings = {item.master_device_id: item for item in _latest_vehicle_readings()}
    trucks = []
    for truck in trucks_qs:
        master_device = getattr(truck, "master_device", None)
        latest = latest_readings.get(getattr(master_device, "id", None))
        trucks.append(
            {
                "id": truck.id,
                "plate": truck.plate,
                "brand": truck.brand,
                "status": truck.status,
                "lat": float(latest.latitude) if latest and latest.latitude is not None else float(truck.latitude),
                "lon": float(latest.longitude) if latest and latest.longitude is not None else float(truck.longitude),
                "speed": round(latest.speed_mph, 1) if latest else 0,
                "heading": round(latest.heading, 1) if latest else 0,
                "active_alert": "",
                "route_id": "",
                "route_name": "",
                "is_demo": False,
            }
        )
    return trucks


def _corridor_points_for_trucks(trucks):
    points = []
    route_ids = {truck.get("route_id") for truck in trucks if truck.get("route_id")}
    demo_routes_by_id = {}
    if route_ids:
        demo_routes_by_id = {route["id"]: route for route in _load_demo_routes(limit=18)}

    for truck in trucks:
        route = demo_routes_by_id.get(truck.get("route_id"))
        if route and route.get("coords"):
            for lat, lon in _sample_route_coords(route["coords"], max_points=14):
                points.append({"lat": lat, "lon": lon, "plate": truck["plate"], "route_name": route.get("name") or truck.get("route_name") or truck["plate"]})
        elif truck.get("lat") is not None and truck.get("lon") is not None:
            points.append({"lat": truck["lat"], "lon": truck["lon"], "plate": truck["plate"], "route_name": truck.get("route_name") or truck["plate"]})

    unique_points = []
    seen = set()
    for point in points:
        key = (round(point["lat"], 2), round(point["lon"], 2), point.get("route_name", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_points.append(point)
    return unique_points[:220]


def _service_heatmap(corridor_points, amenity_payload):
    scored_points = []
    for point in corridor_points:
        matches = _nearby_amenity_matches(point["lat"], point["lon"], amenity_payload, max_results=14)
        raw_score, breakdown, group_breakdown, nearest_by_type, nearest_by_group = _coverage_breakdown(matches)
        scored_points.append(
            {
                **point,
                "raw_score": raw_score,
                "breakdown": breakdown,
                "group_breakdown": group_breakdown,
                "nearby_services": matches[:5],
                "nearest_by_type": nearest_by_type,
                "nearest_by_group": nearest_by_group,
            }
        )

    max_raw = max((item["raw_score"] for item in scored_points), default=0.0)
    heat_points = []
    hubs = []

    for item in scored_points:
        normalized = (item["raw_score"] / max_raw) if max_raw else 0.0
        normalized = round(_clamp(normalized, 0.0, 1.0), 3)
        item["coverage_score"] = normalized
        item["coverage_label"] = _coverage_label(normalized)
        heat_points.append([item["lat"], item["lon"], max(0.08, normalized)])

    for item in sorted(scored_points, key=lambda entry: entry["coverage_score"], reverse=True):
        if item["coverage_score"] <= 0.15:
            continue
        if any(_haversine_miles(item["lat"], item["lon"], hub["lat"], hub["lon"]) < 95 for hub in hubs):
            continue
        hubs.append(
            {
                "name": f"Hub {item['coverage_label']}",
                "lat": item["lat"],
                "lon": item["lon"],
                "radius": 42000,
                "score": item["coverage_score"],
                "color": _coverage_color(item["coverage_score"]),
                "breakdown": item["breakdown"],
                "group_breakdown": item.get("group_breakdown") or {},
                "route_name": item.get("route_name") or "",
                "nearest_by_type": item.get("nearest_by_type") or {},
                "nearest_by_group": item.get("nearest_by_group") or {},
            }
        )
        if len(hubs) >= 8:
            break

    return heat_points, hubs, scored_points


def _fetch_weather_alerts(reference_points, max_items=18):
    now = time.time()
    if now - _GEO_WEATHER_CACHE["timestamp"] < 600 and _GEO_WEATHER_CACHE["items"]:
        return _GEO_WEATHER_CACHE["items"][:max_items]

    try:
        response = requests.get(
            "https://api.weather.gov/alerts/active",
            headers={"User-Agent": "PIN-Platform-Geospatial/0.1"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    severe_terms = (
        "storm",
        "flood",
        "wind",
        "tornado",
        "hurricane",
        "blizzard",
        "snow",
        "ice",
        "fire",
        "heat",
        "dust",
    )
    alerts = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        event_name = str(properties.get("event") or "").strip()
        if not event_name:
            continue
        if not any(term in event_name.lower() for term in severe_terms) and _weather_rank(properties.get("severity")) < 3:
            continue
        center = _geom_center(feature.get("geometry") or {})
        if not center:
            continue
        min_distance = min(
            (_haversine_miles(center[0], center[1], point["lat"], point["lon"]) for point in reference_points),
            default=9999,
        )
        alerts.append(
            {
                "id": properties.get("id") or event_name,
                "lat": center[0],
                "lon": center[1],
                "event": event_name,
                "severity": properties.get("severity") or "Minor",
                "headline": properties.get("headline") or event_name,
                "area_desc": properties.get("areaDesc") or "",
                "description": (properties.get("description") or "")[:260],
                "source": "NWS Live",
                "distance_miles": round(min_distance, 1),
                "color": _weather_color(properties.get("severity")),
            }
        )

    alerts.sort(key=lambda item: (-_weather_rank(item["severity"]), item["distance_miles"]))
    selected = alerts[:max_items]
    _GEO_WEATHER_CACHE["timestamp"] = now
    _GEO_WEATHER_CACHE["items"] = selected
    return selected


def _closure_events(reference_points, weather_alerts, max_items=10):
    closure_terms = (
        "blizzard",
        "ice",
        "winter",
        "flood",
        "tornado",
        "hurricane",
        "dust",
        "high wind",
        "fire",
    )
    closures = []
    for alert in weather_alerts:
        if not any(term in alert["event"].lower() for term in closure_terms):
            continue
        closures.append(
            {
                "id": f"closure-{alert['id']}",
                "lat": alert["lat"],
                "lon": alert["lon"],
                "title": "Cierre / restricción operativa",
                "reason": alert["event"],
                "severity": alert["severity"],
                "headline": alert["headline"],
                "source": alert["source"],
                "color": alert["color"],
            }
        )
        if len(closures) >= max_items:
            break

    if closures:
        return closures

    fallback = []
    for index, point in enumerate(reference_points[:max_items], start=1):
        fallback.append(
            {
                "id": f"closure-fallback-{index}",
                "lat": point["lat"],
                "lon": point["lon"],
                "title": "Restricción operativa preventiva",
                "reason": "Corredor con baja cobertura de servicios",
                "severity": "Moderate",
                "headline": "Monitorear ruta antes de despachar",
                "source": "Analítica PIN",
                "color": "#94a3b8",
            }
        )
    return fallback


def _current_truck_scores(trucks, amenity_payload):
    scored_trucks = []
    max_raw = 0.0
    for truck in trucks:
        matches = _nearby_amenity_matches(truck["lat"], truck["lon"], amenity_payload, max_results=14)
        raw_score, breakdown, group_breakdown, nearest_by_type, nearest_by_group = _coverage_breakdown(matches)
        scored_trucks.append((truck, raw_score, breakdown, group_breakdown, nearest_by_type, nearest_by_group, matches[:5]))
        max_raw = max(max_raw, raw_score)

    normalized_trucks = []
    for truck, raw_score, breakdown, group_breakdown, nearest_by_type, nearest_by_group, nearby_services in scored_trucks:
        normalized = round((raw_score / max_raw) if max_raw else 0.0, 3)
        normalized_trucks.append(
            {
                **truck,
                "coverage_score": normalized,
                "coverage_label": _coverage_label(normalized),
                "breakdown": breakdown,
                "group_breakdown": group_breakdown,
                "nearest_by_type": nearest_by_type,
                "nearest_by_group": nearest_by_group,
                "nearby_services": nearby_services,
            }
        )
    return normalized_trucks


def _amenity_markers(scored_points, max_markers=90):
    markers = []
    seen = set()
    for point in sorted(scored_points, key=lambda entry: entry["coverage_score"], reverse=True):
        for service in point.get("nearby_services") or []:
            key = (service["type"], round(service["lat"], 4), round(service["lon"], 4), service["name"])
            if key in seen:
                continue
            seen.add(key)
            markers.append(
                {
                    "name": service["name"],
                    "type": service["type"],
                    "lat": service["lat"],
                    "lon": service["lon"],
                    "distance_miles": service["distance_miles"],
                    "weight": service["weight"],
                    "extra": service.get("extra") or {},
                }
            )
            if len(markers) >= max_markers:
                return markers
    return markers


def _geoespatial_payload(demo_mode=True):
    trucks = _fleet_snapshot(demo_mode=demo_mode)
    amenity_payload = _amenity_sites()
    corridor_points = _corridor_points_for_trucks(trucks)
    heat_points, service_hubs, scored_points = _service_heatmap(corridor_points, amenity_payload)
    trucks = _current_truck_scores(trucks, amenity_payload)
    amenity_markers = _amenity_markers(scored_points)
    weather_alerts = _fetch_weather_alerts(corridor_points or [{"lat": 39.0, "lon": -96.0}], max_items=18)
    road_closures = _closure_events(
        [item for item in sorted(scored_points, key=lambda entry: entry["coverage_score"])[:10]] or corridor_points,
        weather_alerts,
        max_items=10,
    )

    nearby_closures = 0
    for truck in trucks:
        if any(_haversine_miles(truck["lat"], truck["lon"], item["lat"], item["lon"]) <= 65 for item in road_closures):
            nearby_closures += 1

    return {
        "trucks": trucks,
        "service_heatmap": heat_points,
        "service_hubs": service_hubs,
        "amenity_markers": amenity_markers,
        "weather_alerts": weather_alerts,
        "road_closures": road_closures,
        "kpis": {
            "active_geofences": len(service_hubs),
            "weather_alerts": len(weather_alerts),
            "route_deviations": nearby_closures,
            "restricted_zones": len(road_closures),
        },
        "meta": {
            "last_updated": timezone.now().strftime("%H:%M:%S"),
            "demo_mode": demo_mode,
        },
    }


class DashboardsHubView(TemplateView):
    template_name = "dashboards/hub.html"


class ResumenView(TemplateView):
    template_name = "dashboards/resumen.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_trucks = Truck.objects.count()
        active_trucks = Truck.objects.filter(status="ACTIVE").count()
        maintenance_trucks = Truck.objects.filter(status="MAINTENANCE").count()
        inactive_trucks = max(total_trucks - active_trucks - maintenance_trucks, 0)

        context["total_trucks"] = total_trucks
        context["active_trucks"] = active_trucks
        context["maintenance_trucks"] = maintenance_trucks
        context["inactive_trucks"] = inactive_trucks
        context["active_trips"] = Trip.objects.filter(status="IN_TRANSIT").count()
        context["completed_trips"] = Trip.objects.filter(status="COMPLETED").count()
        context["hos_alerts"] = HOSAlert.objects.filter(status="ACTIVE").count()
        context["weight_alerts"] = WeightInspection.objects.filter(is_overweight=True).count()
        context["fleet_status_json"] = {
            "labels": ["Activos", "En Mantenimiento", "Inactivos"],
            "values": [active_trucks, maintenance_trucks, inactive_trucks],
        }
        context["trucks_map_json"] = _truck_map_data()
        return context


class MonitoreoIoTView(TemplateView):
    template_name = "dashboards/monitoreo_iot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        window_24h = now - timedelta(hours=24)
        window_2h = now - timedelta(hours=2)

        master_devices = MasterDevice.objects.select_related("truck").all()
        active_sensor_count = TireSensor.objects.filter(is_active=True).count()
        online_devices = master_devices.filter(status="ONLINE").count()
        total_devices = master_devices.count()

        context["active_sensors"] = active_sensor_count + total_devices
        context["data_processed_24h"] = (
            TireReading.objects.filter(timestamp__gte=window_24h).count()
            + VehicleReading.objects.filter(timestamp__gte=window_24h).count()
        )
        context["system_latency"] = 0
        context["network_health"] = round((online_devices / total_devices) * 100, 1) if total_devices else 0

        recent_hourly_data = list(
            TireReading.objects.filter(timestamp__gte=window_2h)
            .annotate(hour=TruncHour("timestamp"))
            .values("hour")
            .annotate(avg_pressure=Avg("pressure_psi"), avg_temp=Avg("temperature_f"))
            .order_by("hour")
        )
        if recent_hourly_data:
            series_data = recent_hourly_data
        else:
            latest_available = list(TireReading.objects.order_by("-timestamp")[:24])
            latest_available.reverse()
            series_data = [
                {
                    "hour": item.timestamp,
                    "avg_pressure": item.pressure_psi,
                    "avg_temp": item.temperature_f,
                }
                for item in latest_available
            ]

        context["iot_timeseries_json"] = {
            "times": [item["hour"].strftime("%m-%d %H:%M") for item in series_data],
            "pressure": [round(item["avg_pressure"] or 0, 1) for item in series_data],
            "temp": [round(item["avg_temp"] or 0, 1) for item in series_data],
            "has_live_window": bool(recent_hourly_data),
            "has_data": bool(series_data),
        }

        fleet_list = []
        for master in master_devices[:50]:
            stats = TireReading.objects.filter(
                sensor__master_device=master,
                timestamp__gte=window_24h,
            ).aggregate(
                avg_temp=Avg("temperature_f"),
                avg_psi=Avg("pressure_psi"),
                avg_wear=Avg("estimated_tread_depth"),
            )
            fleet_list.append(
                {
                    "id": master.truck.id,
                    "plate": master.truck.plate,
                    "brand": master.truck.brand,
                    "model": master.truck.model,
                    "status": master.status,
                    "last_ping": _time_ago_label(master.last_ping),
                    "avg_temp": round(stats["avg_temp"] or 0, 1),
                    "avg_psi": round(stats["avg_psi"] or 0, 1),
                    "avg_wear": round(stats["avg_wear"] or 0, 1),
                }
            )

        context["fleet_list"] = fleet_list
        context["fleet_list_json"] = fleet_list
        return context


class AlertasView(TemplateView):
    template_name = "dashboards/alertas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alertas = []

        for alert in HOSAlert.objects.select_related("driver").filter(status="ACTIVE")[:8]:
            alertas.append(
                {
                    "id": f"HOS-{alert.id}",
                    "truck": "N/A",
                    "brand": "HOS",
                    "type": alert.get_alert_type_display(),
                    "sensor": "Conductor",
                    "severity": "CRITICAL" if alert.severity == "VIOLATION" else "WARNING",
                    "time": _time_ago_label(alert.timestamp),
                }
            )

        for inspection in WeightInspection.objects.select_related("truck").filter(is_overweight=True)[:8]:
            alertas.append(
                {
                    "id": f"WGT-{inspection.id}",
                    "truck": inspection.truck.plate,
                    "brand": inspection.truck.brand,
                    "type": "Exceso de Peso",
                    "sensor": inspection.inspection_type,
                    "severity": "CRITICAL",
                    "time": _time_ago_label(inspection.timestamp),
                }
            )

        mantenimientos = []
        for log in TireMaintenanceLog.objects.select_related("sensor__master_device__truck")[:8]:
            truck = log.sensor.master_device.truck
            mantenimientos.append(
                {
                    "id": f"WO-{log.id}",
                    "truck": truck.plate,
                    "type": log.maintenance_type,
                    "status": "COMPLETED",
                    "eta": log.timestamp.strftime("%Y-%m-%d"),
                }
            )

        context["alertas"] = alertas
        context["mantenimientos"] = mantenimientos
        context["criticas_count"] = sum(1 for item in alertas if item["severity"] == "CRITICAL")
        context["warning_count"] = sum(1 for item in alertas if item["severity"] == "WARNING")
        context["mantenimiento_count"] = len(mantenimientos)
        return context


class HOSComplianceView(TemplateView):
    template_name = "dashboards/hos_compliance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_drivers = Driver.objects.filter(status="ACTIVE").count()
        active_violations = HOSAlert.objects.filter(status="ACTIVE").count()
        avg_drive_minutes = HOSCompliance.objects.aggregate(avg_minutes=Avg("driving_time_today"))["avg_minutes"] or 0
        compliant = HOSCompliance.objects.filter(is_compliant=True).count()
        compliance_score = round((compliant / total_drivers) * 100, 1) if total_drivers else 0

        duty_counts = {
            item["status"]: item["total"]
            for item in DriverLog.objects.values("status").annotate(total=Sum(1))
        }
        timeline = (
            HOSAlert.objects.filter(timestamp__gte=timezone.now() - timedelta(days=7))
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(total=Sum(1))
            .order_by("day")
        )

        risk_drivers = []
        for alert in HOSAlert.objects.select_related("driver").filter(status="ACTIVE")[:10]:
            risk_drivers.append(
                {
                    "name": f"{alert.driver.first_name} {alert.driver.last_name}",
                    "truck": "N/A",
                    "rule": alert.get_alert_type_display(),
                    "time_left": "Infracción activa",
                    "status": "Crítico" if alert.severity == "VIOLATION" else "Alerta",
                    "action": "Contactar Inmediato" if alert.severity == "VIOLATION" else "Monitorear",
                }
            )

        context["kpis"] = {
            "active_drivers": total_drivers,
            "hos_violations": active_violations,
            "avg_drive_time": _minutes_to_label(avg_drive_minutes),
            "compliance_score": f"{compliance_score}%",
        }
        context["duty_labels"] = ["Driving", "On-Duty", "Sleeper Berth", "Off-Duty"]
        context["duty_values"] = [
            duty_counts.get("DRIVING", 0),
            duty_counts.get("ON_DUTY", 0),
            duty_counts.get("SLEEPER", 0),
            duty_counts.get("OFF_DUTY", 0),
        ]
        context["timeline_hours"] = [item["day"].strftime("%b %d") for item in timeline]
        context["timeline_risk"] = [item["total"] for item in timeline]
        context["risk_drivers"] = risk_drivers
        return context


class DesgasteLlantasView(TemplateView):
    template_name = "dashboards/desgaste_llantas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_readings = list(_latest_tire_readings().filter(estimated_tread_depth__isnull=False))
        total_tires = TireSensor.objects.filter(is_active=True).count()
        critical = sum(1 for item in latest_readings if (item.estimated_tread_depth or 0) < 5)
        warning = sum(1 for item in latest_readings if 5 <= (item.estimated_tread_depth or 0) < 10)
        good = max(total_tires - critical - warning, 0)

        context["total_tires_monitored"] = total_tires
        context["critical_wear"] = critical
        context["warning_wear"] = warning
        context["good_wear"] = good
        context["wear_distribution_json"] = {
            "labels": ["Óptimo (>10/32\")", "Advertencia (5/32\"-10/32\")", "Crítico (<5/32\")"],
            "values": [good, warning, critical],
        }

        forecast = (
            TireMaintenanceLog.objects.filter(timestamp__gte=timezone.now() - timedelta(days=180))
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(total=Sum(1))
            .order_by("day")
        )
        context["replacement_forecast_json"] = {
            "months": [item["day"].strftime("%b %Y") for item in forecast],
            "replacements": [item["total"] for item in forecast],
        }

        top_wear_trucks = []
        for reading in sorted(latest_readings, key=lambda item: item.estimated_tread_depth or 99)[:5]:
            truck = reading.sensor.master_device.truck
            top_wear_trucks.append(
                {
                    "plate": truck.plate,
                    "worst_tire": reading.sensor.position,
                    "tread_depth": round(reading.estimated_tread_depth or 0, 1),
                    "est_miles_left": max(int((reading.estimated_tread_depth or 0) * 1000), 0),
                }
            )
        context["top_wear_trucks"] = top_wear_trucks
        return context


class PesoVehiculoView(TemplateView):
    template_name = "dashboards/peso_vehiculo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        inspections = WeightInspection.objects.select_related("truck")
        weigh_ins_24h = inspections.filter(timestamp__gte=now - timedelta(hours=24)).count()
        overweight = inspections.filter(is_overweight=True)
        avg_gross_weight = inspections.aggregate(value=Avg("gross_weight"))["value"] or 0

        trend = (
            overweight.filter(timestamp__gte=now - timedelta(days=7))
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(total=Sum(1))
            .order_by("day")
        )

        steer_total = drive_total = trailer_total = 0
        axle_samples = 0
        for inspection in inspections[:50]:
            weights = inspection.axle_weights or {}
            steer_total += weights.get("steer", 0)
            drive_total += weights.get("drive", 0)
            trailer_total += weights.get("trailer", 0)
            axle_samples += 1

        context["weigh_ins_24h"] = weigh_ins_24h
        context["overweight_violations"] = overweight.count()
        context["avg_gross_weight"] = round(avg_gross_weight, 0)
        context["wim_bypasses"] = 0
        context["weight_trend_json"] = {
            "days": [item["day"].strftime("%b %d") for item in trend],
            "violations": [item["total"] for item in trend],
        }
        context["axle_distribution_json"] = {
            "labels": ["Steer (Dirección)", "Drive (Tracción)", "Trailer (Remolque)"],
            "values": [
                round(steer_total / axle_samples, 0) if axle_samples else 0,
                round(drive_total / axle_samples, 0) if axle_samples else 0,
                round(trailer_total / axle_samples, 0) if axle_samples else 0,
            ],
        }
        context["heavy_trucks"] = [
            {
                "plate": inspection.truck.plate,
                "location": inspection.location,
                "gross_weight": round(inspection.gross_weight, 0),
                "status": "VIOLATION" if inspection.is_overweight else "OK",
            }
            for inspection in inspections.order_by("-timestamp")[:8]
        ]
        return context


class RecomendacionesView(TemplateView):
    template_name = "dashboards/recomendaciones.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trucks = Truck.objects.all()[:15]
        fleet_data = {}

        global_recs = []
        critical_tires = _latest_tire_readings().filter(estimated_tread_depth__lt=5).count()
        overweight_count = WeightInspection.objects.filter(is_overweight=True).count()
        hos_active = HOSAlert.objects.filter(status="ACTIVE").count()

        if critical_tires:
            global_recs.append(
                _recommendation(
                    "Rotación y cambio prioritario",
                    f"Se detectan {critical_tires} sensores con profundidad crítica de banda.",
                    "Reduce riesgo de reventón",
                    "HIGH",
                    "fa-triangle-exclamation",
                    "#ef4444",
                )
            )
        if overweight_count:
            global_recs.append(
                _recommendation(
                    "Revisión de carga",
                    f"Hay {overweight_count} inspecciones con sobrepeso registradas.",
                    "Reduce multas DOT",
                    "MEDIUM",
                    "fa-weight-scale",
                    "#f59e0b",
                )
            )
        if hos_active:
            global_recs.append(
                _recommendation(
                    "Monitoreo HOS reforzado",
                    f"Existen {hos_active} alertas HOS activas.",
                    "Evita incumplimientos FMCSA",
                    "MEDIUM",
                    "fa-clock",
                    "#3b82f6",
                )
            )

        fleet_data["GLOBAL"] = {
            "plate": "GLOBAL",
            "dropdown_label": "Flota Global",
            "kpis": {
                "efficiency": max(0, 100 - (critical_tires * 2) - hos_active),
                "fuel": round(VehicleReading.objects.aggregate(avg=Avg("obd_fuel_level"))["avg"] or 0, 1),
                "incidents": overweight_count + hos_active,
                "optimizations": len(global_recs),
            },
            "radar": [
                max(0, 100 - (critical_tires * 5)),
                max(0, 100 - (overweight_count * 10)),
                max(0, 100 - (hos_active * 10)),
                100 if Trip.objects.exists() else 0,
                TruckStop.objects.count(),
                AlternativeFuelStation.objects.count(),
            ],
            "recs": global_recs,
        }

        for truck in trucks:
            truck_alerts = WeightInspection.objects.filter(truck=truck, is_overweight=True).count()
            truck_tires = _latest_tire_readings().filter(sensor__master_device__truck=truck)
            low_tread = truck_tires.filter(estimated_tread_depth__lt=5).count()
            recs = []
            if low_tread:
                recs.append(
                    _recommendation(
                        "Cambio de llantas prioritario",
                        f"La unidad {truck.plate} tiene {low_tread} lecturas en zona crítica.",
                        "Prevención de incidente",
                        "HIGH",
                        "fa-ban",
                        "#ef4444",
                    )
                )
            if truck_alerts:
                recs.append(
                    _recommendation(
                        "Validar distribución de carga",
                        f"La unidad {truck.plate} registra eventos de sobrepeso.",
                        "Cumplimiento regulatorio",
                        "MEDIUM",
                        "fa-weight-scale",
                        "#f59e0b",
                    )
                )
            if not recs:
                recs.append(
                    _recommendation(
                        "Operación estable",
                        f"La unidad {truck.plate} no presenta alertas críticas activas.",
                        "Mantener monitoreo",
                        "LOW",
                        "fa-check-circle",
                        "#10b981",
                    )
                )

            incident_count = truck_alerts + low_tread
            fleet_data[truck.plate] = {
                "plate": truck.plate,
                "dropdown_label": f"{truck.plate} - {truck.brand}",
                "kpis": {
                    "efficiency": max(0, 100 - incident_count * 15),
                    "fuel": round(
                        VehicleReading.objects.filter(master_device__truck=truck).aggregate(avg=Avg("obd_fuel_level"))["avg"] or 0,
                        1,
                    ),
                    "incidents": incident_count,
                    "optimizations": len(recs),
                },
                "radar": [
                    max(0, 100 - low_tread * 20),
                    max(0, 100 - truck_alerts * 20),
                    100 if truck.status == "ACTIVE" else 60,
                    TireReading.objects.filter(sensor__master_device__truck=truck).count(),
                    100,
                    100,
                ],
                "recs": recs,
            }

        context["fleet_data_json"] = fleet_data
        context["trucks_list"] = [{"plate": key, "label": value["dropdown_label"]} for key, value in fleet_data.items() if key != "GLOBAL"]
        return context


class GeoespacialView(TemplateView):
    template_name = "dashboards/geoespacial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demo_mode = self.request.GET.get("demo") != "0"
        payload = _geoespatial_payload(demo_mode=demo_mode)

        context["active_geofences"] = payload["kpis"]["active_geofences"]
        context["weather_alerts"] = payload["kpis"]["weather_alerts"]
        context["route_deviations"] = payload["kpis"]["route_deviations"]
        context["restricted_zones"] = payload["kpis"]["restricted_zones"]
        context["trucks_map_json"] = payload["trucks"]
        context["geofences_json"] = payload["service_hubs"]
        context["heatmap_json"] = payload["service_heatmap"]
        context["amenity_markers_json"] = payload["amenity_markers"]
        context["weather_alerts_json"] = payload["weather_alerts"]
        context["road_closures_json"] = payload["road_closures"]
        context["geospatial_meta_json"] = payload["meta"]
        return context


def api_geoespacial_live(request):
    demo_mode = request.GET.get("demo") != "0"
    return JsonResponse(_geoespatial_payload(demo_mode=demo_mode))


class EstacionesDescansoView(TemplateView):
    template_name = "dashboards/estaciones_descanso.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = _station_dashboard_payload()
        summary = payload["summary"]

        context["total_stations"] = f"{summary['total_stations']:,}"
        context["states_covered"] = f"{summary['states_covered']:,}"
        context["total_parking_spots"] = f"{summary['total_parking_spots']:,}"
        context["available_spots"] = f"{summary['available_spots']:,}"
        context["occupancy_rate"] = summary["occupancy_rate"]
        context["estimated_method"] = summary["estimated_method"]
        context["top_operator"] = summary["top_operator"]
        context["top_operator_share"] = summary["top_operator_share"]
        context["amenities_labels"] = payload["amenities_labels"]
        context["amenities_values"] = payload["amenities_values"]
        context["operator_labels"] = payload["operator_labels"]
        context["operator_values"] = payload["operator_values"]
        context["occupancy_hours"] = payload["occupancy_hours"]
        context["occupancy_values"] = payload["occupancy_values"]
        context["top_stations"] = payload["top_stations"]
        context["station_markers"] = payload["map_markers"]
        return context


class CombustibleReciclajeView(TemplateView):
    template_name = "dashboards/combustible_reciclaje.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_stats = TransportationStatistic.objects.first()
        recycled_tons = RecyclingFacility.objects.aggregate(total=Sum("tires_recycled_tons"))["total"] or 0
        stats_history = list(TransportationStatistic.objects.order_by("-date")[:6])
        stats_history.reverse()

        context["kpis"] = {
            "co2_saved": f"{round(float(recycled_tons), 0):,.0f}",
            "tires_recycled": RecyclingFacility.objects.count(),
            "fuel_efficiency": f"{round(VehicleReading.objects.aggregate(avg=Avg('obd_fuel_level'))['avg'] or 0, 1)}",
            "green_score": AlternativeFuelStation.objects.count(),
        }
        context["tires_destiny_labels"] = ["Renovado (Retread)", "Reciclaje (Asfalto/Caucho)", "Desecho (Vertedero)"]
        context["tires_destiny_values"] = [0, round(float(recycled_tons), 0), 0]
        context["fuel_trend_months"] = [item.date.strftime("%b") for item in stats_history]
        context["fuel_consumption"] = [float(item.diesel_price or 0) for item in stats_history]
        context["epa_audit"] = [
            {
                "unit": truck.plate,
                "mpg": "N/D",
                "status": "Crítico" if HOSAlert.objects.filter(driver__status="ACTIVE", status="ACTIVE").exists() else "Óptimo",
                "co2": f"{float(latest_stats.diesel_price) if latest_stats and latest_stats.diesel_price else 0}",
                "action": "Revisar telemetría" if TireReading.objects.filter(sensor__master_device__truck=truck).exists() else "Sin datos IoT",
            }
            for truck in Truck.objects.all()[:10]
        ]
        return context


class RegulacionSeguridadView(TemplateView):
    template_name = "dashboards/regulacion_seguridad.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_enforcement = WeightEnforcementStatistic.objects.first()
        active_hos = HOSAlert.objects.filter(status="ACTIVE").count()
        overweight = WeightInspection.objects.filter(is_overweight=True).count()
        weighed_total = (
            (latest_enforcement.vehicles_weighed_fixed + latest_enforcement.vehicles_weighed_wim)
            if latest_enforcement
            else 0
        )
        oos_rate = round((overweight / weighed_total) * 100, 1) if weighed_total else 0

        context["kpis"] = {
            "csa_score": overweight + active_hos,
            "dot_inspections": weighed_total,
            "oos_rate": f"{oos_rate:.1f}%",
            "safety_warnings": active_hos,
        }
        context["csa_labels"] = ["Unsafe Driving", "Crash Indicator", "HOS Compliance", "Vehicle Maint.", "Ctrl. Substances", "Driver Fitness"]
        context["csa_values"] = [
            overweight,
            0,
            active_hos,
            TireMaintenanceLog.objects.count(),
            0,
            Driver.objects.filter(status="SUSPENDED").count(),
        ]
        context["dot_levels"] = ["Level I (Full)", "Level II (Walk-Around)", "Level III (Driver/Cred)"]
        context["dot_counts"] = [
            latest_enforcement.vehicles_weighed_fixed if latest_enforcement else 0,
            latest_enforcement.vehicles_weighed_wim if latest_enforcement else 0,
            overweight,
        ]

        recent_violations = []
        for inspection in WeightInspection.objects.select_related("truck").order_by("-timestamp")[:5]:
            recent_violations.append(
                {
                    "date": inspection.timestamp.strftime("%Y-%m-%d"),
                    "unit": inspection.truck.plate,
                    "type": "Exceso de Peso" if inspection.is_overweight else "Inspección",
                    "severity": "OOS (Out of Service)" if inspection.is_overweight else "Advertencia",
                    "status": "Pendiente" if inspection.is_overweight else "Registrado",
                }
            )
        context["recent_violations"] = recent_violations
        return context


class ModelosPredictivosView(TemplateView):
    template_name = "dashboards/modelos_predictivos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = _predictive_dashboard_payload()
        context["kpis"] = payload["kpis"]
        context["forecast_days"] = payload["forecast_days"]
        context["risk_fleet_a"] = payload["risk_fleet_a"]
        context["risk_fleet_b"] = payload["risk_fleet_b"]
        context["tire_scatter_json"] = payload["tire_scatter_json"]
        context["upcoming_failures"] = payload["upcoming_failures"]
        context["prediction_records"] = payload["prediction_records"]
        return context
