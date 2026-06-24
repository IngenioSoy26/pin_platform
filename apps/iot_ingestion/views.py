from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.services import AlertEngine
from apps.devices.models import MasterDevice, TireSensor, VehicleReading
from apps.recommendations.services import RecommendationEngine
from apps.tires.models import TireReading

class IoTReadingIngestionView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        device_code = data.get("device_code")

        try:
            master_device = MasterDevice.objects.get(device_code=device_code)
        except MasterDevice.DoesNotExist:
            return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

        timestamp = parse_datetime(data.get("timestamp")) if data.get("timestamp") else None
        timestamp = timestamp or timezone.now()
        truck = master_device.truck
        v_data = data.get("vehicle_data", {})
        created_alerts = []
        created_recommendations = []
        missing_sensors = []

        with transaction.atomic():
            VehicleReading.objects.create(
                master_device=master_device,
                timestamp=timestamp,
                latitude=v_data.get("latitude"),
                longitude=v_data.get("longitude"),
                speed_mph=v_data.get("speed_mph") or 0,
                heading=v_data.get("heading") or 0,
                obd_rpm=v_data.get("rpm"),
                obd_fuel_level=v_data.get("fuel_level"),
                accel_x=v_data.get("accel_x"),
                accel_y=v_data.get("accel_y"),
                accel_z=v_data.get("accel_z"),
                battery_voltage=v_data.get("battery_level"),
            )

            if v_data.get("latitude") is not None and v_data.get("longitude") is not None:
                truck.latitude = v_data.get("latitude")
                truck.longitude = v_data.get("longitude")
                truck.save(update_fields=["latitude", "longitude", "updated_at"])

            master_device.battery_level = v_data.get("battery_level", master_device.battery_level)
            master_device.signal_strength = v_data.get("signal_strength", master_device.signal_strength)
            master_device.last_ping = timestamp
            master_device.status = "ONLINE"
            master_device.save(update_fields=["battery_level", "signal_strength", "last_ping", "status", "updated_at"])

            if master_device.battery_level is not None and master_device.battery_level < 20:
                created_alerts.append(
                    AlertEngine.create_alert(
                        truck=truck,
                        alert_type="LOW_BATTERY_MASTER",
                        severity="HIGH",
                        title=f"Bateria baja del dispositivo maestro {master_device.device_code}",
                        message="El dispositivo maestro requiere recarga o revision electrica.",
                        trigger_value=master_device.battery_level,
                        threshold_value=20.0,
                        unit="%",
                    )
                )

            accel_x = v_data.get("accel_x")
            if accel_x is not None and accel_x <= -2.5:
                created_alerts.append(
                    AlertEngine.create_alert(
                        truck=truck,
                        alert_type="HARD_BRAKING",
                        severity="MEDIUM",
                        title=f"Frenado brusco en {truck.plate}",
                        message="La telemetria detecto una desaceleracion brusca.",
                        trigger_value=accel_x,
                        threshold_value=-2.5,
                        unit="g",
                    )
                )

            tire_readings_data = data.get("tire_readings", [])
            for tr_data in tire_readings_data:
                position = tr_data.get("position")
                try:
                    sensor = TireSensor.objects.get(master_device=master_device, position=position)
                except TireSensor.DoesNotExist:
                    missing_sensors.append(position)
                    continue

                reading = TireReading.objects.create(
                    sensor=sensor,
                    timestamp=timestamp,
                    pressure_psi=tr_data.get("pressure_psi") or 0,
                    temperature_f=tr_data.get("temperature_f") or 0,
                    vibration_g=tr_data.get("vibration_g", 0.0),
                    estimated_tread_depth=tr_data.get("estimated_tread_depth"),
                    rssi=tr_data.get("rssi"),
                    sensor_battery=tr_data.get("battery_level"),
                )
                created_alerts.extend(AlertEngine.check_tire_alerts(reading))

            unique_alerts = []
            seen_ids = set()
            for alert in created_alerts:
                if alert and alert.id not in seen_ids:
                    unique_alerts.append(alert)
                    seen_ids.add(alert.id)

            for alert in unique_alerts:
                created_recommendations.extend(RecommendationEngine.generate_recommendations(alert))

        return Response(
            {
                "status": "success",
                "message": "Data ingested successfully",
                "alerts_generated": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "title": alert.title,
                        "severity": alert.severity,
                    }
                    for alert in unique_alerts
                ],
                "recommendations_generated": [
                    {
                        "id": recommendation.id,
                        "type": recommendation.rec_type,
                        "target_name": recommendation.target_name,
                    }
                    for recommendation in created_recommendations
                ],
                "missing_sensors": missing_sensors,
            },
            status=status.HTTP_201_CREATED,
        )
