from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone

from apps.devices.models import VehicleReading
from apps.routes.services import RouteService
from apps.tires.models import TireMaintenanceLog, TirePositionConfig, TireReading
from apps.weight_monitoring.models import WeightInspection

from .wear_formulas import calcular_desgaste

class TireWearCalculator:
    """
    Servicio que implementa la lógica predictiva física de desgaste de llantas.
    """

    @staticmethod
    def calculate_wear(miles, base_rate, factors):
        """
        Calcula el desgaste de una llanta en un periodo específico.
        """
        return calcular_desgaste(miles, base_rate, **factors)
    
    @staticmethod
    def predict_remaining_life(sensor):
        """
        Calcula la vida útil restante estimada en millas y días
        basado en la profundidad actual y la tasa de desgaste histórica.
        """
        latest_reading = sensor.readings.filter(estimated_tread_depth__isnull=False).order_by("-timestamp").first()
        config = TirePositionConfig.objects.filter(position=sensor.position).first()
        if latest_reading is None or config is None:
            return {
                "miles_remaining": max(sensor.lifecycle_km - sensor.accumulated_km, 0),
                "days_remaining": None,
                "estimated_tread_depth": latest_reading.estimated_tread_depth if latest_reading else None,
            }

        factors = TireWearCalculator.get_wear_factors(sensor)
        projected_loss_per_1000 = TireWearCalculator.calculate_wear(
            miles=1000,
            base_rate=config.base_wear_rate,
            factors=factors,
        )
        projected_loss_per_1000 = max(projected_loss_per_1000, 0.01)

        usable_depth = max((latest_reading.estimated_tread_depth or 0) - config.critical_tread_depth, 0)
        miles_remaining = max(int((usable_depth / projected_loss_per_1000) * 1000), 0)

        latest_vehicle = (
            VehicleReading.objects.filter(master_device=sensor.master_device)
            .order_by("-timestamp")
            .first()
        )
        avg_speed = latest_vehicle.speed_mph if latest_vehicle and latest_vehicle.speed_mph else 0
        daily_miles = max(avg_speed * 8, 250) if avg_speed else 250
        days_remaining = round(miles_remaining / daily_miles, 1) if miles_remaining else 0

        return {
            "miles_remaining": miles_remaining,
            "days_remaining": days_remaining,
            "estimated_tread_depth": round(latest_reading.estimated_tread_depth or 0, 2),
            "wear_rate_per_1000_miles": round(projected_loss_per_1000, 4),
        }

    @staticmethod
    def get_wear_factors(sensor):
        """
        Recopila todos los factores de ajuste recientes para un sensor específico.
        """
        latest_reading = sensor.readings.order_by("-timestamp").first()
        latest_vehicle = (
            VehicleReading.objects.filter(master_device=sensor.master_device)
            .order_by("-timestamp")
            .first()
        )
        route_adj = 0.0
        if latest_vehicle:
            route_adj = RouteService.get_adjustment_for_position(
                latest_vehicle.latitude,
                latest_vehicle.longitude,
            )
        config = TirePositionConfig.objects.filter(position=sensor.position).first()
        latest_weight = (
            WeightInspection.objects.filter(truck=sensor.master_device.truck)
            .order_by("-timestamp")
            .first()
        )
        recent_vehicle = VehicleReading.objects.filter(
            master_device=sensor.master_device,
            timestamp__gte=timezone.now() - timedelta(days=7),
        )
        hard_events = recent_vehicle.filter(
            accel_x__isnull=False,
        ).count()
        if hard_events:
            hard_events = recent_vehicle.filter(accel_x__gte=2.5).count() + recent_vehicle.filter(accel_x__lte=-2.5).count()

        maintenance = (
            TireMaintenanceLog.objects.filter(sensor=sensor)
            .order_by("-timestamp")
            .first()
        )
        maint_adj = -0.05 if maintenance and maintenance.timestamp >= timezone.now() - timedelta(days=90) else 0.0
        target_pressure = config.target_pressure if config else 100
        target_temperature = config.target_temperature if config else 110
        nominal_load = config.max_load if config else 4000
        gross_weight = latest_weight.gross_weight if latest_weight else sensor.master_device.truck.num_tires * nominal_load
        current_load = gross_weight / max(sensor.master_device.truck.num_tires, 1)

        return {
            "psi_actual": latest_reading.pressure_psi if latest_reading else target_pressure,
            "psi_recomendado": target_pressure,
            "temp_f": latest_reading.temperature_f if latest_reading else target_temperature,
            "speed_mph": latest_vehicle.speed_mph if latest_vehicle else 55,
            "carga_actual": current_load,
            "carga_nominal": nominal_load,
            "vibration_g": latest_reading.vibration_g if latest_reading else 0.2,
            "hard_events": hard_events,
            "weather_adj": 0.0,
            "route_adj": route_adj,
            "maint_adj": maint_adj,
        }
