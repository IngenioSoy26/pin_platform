from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from apps.core.models import AlternativeFuelStation, RecyclingFacility, TireShop, TruckStop, WIMStation

from .models import Recommendation


def _distance_km(origin_lat, origin_lon, target_lat, target_lon):
    if None in {origin_lat, origin_lon, target_lat, target_lon}:
        return None

    lat1, lon1, lat2, lon2 = map(radians, [origin_lat, origin_lon, target_lat, target_lon])
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    arc = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return 6371 * 2 * asin(sqrt(arc))


class RecommendationEngine:
    @staticmethod
    def _select_target(alert):
        truck = alert.truck
        truck_lat = float(truck.latitude) if truck.latitude is not None else None
        truck_lon = float(truck.longitude) if truck.longitude is not None else None

        if alert.alert_type in {"LOW_PRESSURE", "HIGH_PRESSURE", "PUNCTURE", "TIRE_WEAR_WARNING", "TIRE_WEAR_CRITICAL"}:
            queryset = TireShop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "TIRE_SHOP"
            priority = 9 if alert.severity == "CRITICAL" else 7
        elif alert.alert_type in {"HOS_WARNING", "HOS_VIOLATION"}:
            queryset = TruckStop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "REST_STOP"
            priority = 8
        elif alert.alert_type in {"OVERWEIGHT_AXLE", "OVERWEIGHT_GROSS"}:
            queryset = WIMStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "WIM_STATION"
            priority = 8
        elif alert.alert_type == "HIGH_TEMPERATURE":
            queryset = TireShop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "MECHANIC"
            priority = 8
        elif alert.alert_type == "LOW_BATTERY_SENSOR":
            queryset = TruckStop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "MECHANIC"
            priority = 6
        else:
            queryset = AlternativeFuelStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            rec_type = "ALT_FUEL"
            priority = 5

        best_target = None
        best_distance = None
        for candidate in queryset[:200]:
            candidate_distance = _distance_km(
                truck_lat,
                truck_lon,
                float(candidate.latitude) if candidate.latitude is not None else None,
                float(candidate.longitude) if candidate.longitude is not None else None,
            )
            if candidate_distance is None and best_target is None:
                best_target = candidate
                best_distance = None
            elif candidate_distance is not None and (best_distance is None or candidate_distance < best_distance):
                best_target = candidate
                best_distance = candidate_distance

        return rec_type, priority, best_target, best_distance

    @staticmethod
    def generate_recommendations(alert):
        existing = Recommendation.objects.filter(alert=alert).order_by("-created_at").first()
        if existing:
            return [existing]

        rec_type, priority, target, distance_km = RecommendationEngine._select_target(alert)
        if target is None:
            return []

        return [
            Recommendation.objects.create(
                alert=alert,
                truck=alert.truck,
                rec_type=rec_type,
                priority=priority,
                target_name=target.name,
                target_address=getattr(target, "address", "") or "",
                latitude=float(target.latitude) if getattr(target, "latitude", None) is not None else None,
                longitude=float(target.longitude) if getattr(target, "longitude", None) is not None else None,
                distance_km=round(distance_km, 1) if distance_km is not None else None,
                estimated_time_min=int((distance_km / 80) * 60) if distance_km is not None else None,
                estimated_cost_usd=None,
                reason=alert.message,
            )
        ]
