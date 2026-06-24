from __future__ import annotations

from django.utils import timezone

from apps.hos_monitoring.models import HOSAlert
from apps.hos_monitoring.services import HOSCalculator
from apps.tires.models import TirePositionConfig
from apps.weight_monitoring.models import WeightInspection

from .models import Alert


class AlertEngine:
    @staticmethod
    def create_alert(truck, alert_type, severity, title, message, sensor=None, **kwargs):
        existing = Alert.objects.filter(
            truck=truck,
            sensor=sensor,
            alert_type=alert_type,
            status="ACTIVE",
        ).order_by("-timestamp").first()
        if existing:
            return existing

        return Alert.objects.create(
            truck=truck,
            sensor=sensor,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            **kwargs,
        )

    @staticmethod
    def check_tire_alerts(reading):
        sensor = reading.sensor
        truck = sensor.master_device.truck
        config = TirePositionConfig.objects.filter(position=sensor.position).first()
        alerts = []

        target_pressure = config.target_pressure if config else 100.0
        target_temperature = config.target_temperature if config else 120.0
        warning_tread = config.warning_tread_depth if config else 6.0
        critical_tread = config.critical_tread_depth if config else 4.0

        if reading.pressure_psi <= target_pressure * 0.7:
            alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    sensor=sensor,
                    alert_type="PUNCTURE",
                    severity="CRITICAL",
                    title=f"Pinchazo potencial en {sensor.position}",
                    message=f"La llanta {sensor.position} reporta {reading.pressure_psi:.1f} PSI.",
                    trigger_value=reading.pressure_psi,
                    threshold_value=round(target_pressure * 0.7, 1),
                    unit="PSI",
                )
            )
        elif reading.pressure_psi < target_pressure * 0.9:
            alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    sensor=sensor,
                    alert_type="LOW_PRESSURE",
                    severity="HIGH",
                    title=f"Presion baja en {sensor.position}",
                    message=f"La llanta {sensor.position} esta por debajo de la presion objetivo.",
                    trigger_value=reading.pressure_psi,
                    threshold_value=round(target_pressure * 0.9, 1),
                    unit="PSI",
                )
            )
        elif reading.pressure_psi > target_pressure * 1.1:
            alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    sensor=sensor,
                    alert_type="HIGH_PRESSURE",
                    severity="MEDIUM",
                    title=f"Presion alta en {sensor.position}",
                    message=f"La llanta {sensor.position} supera el rango esperado de presion.",
                    trigger_value=reading.pressure_psi,
                    threshold_value=round(target_pressure * 1.1, 1),
                    unit="PSI",
                )
            )

        if reading.temperature_f >= max(target_temperature, 120.0):
            alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    sensor=sensor,
                    alert_type="HIGH_TEMPERATURE",
                    severity="HIGH" if reading.temperature_f < 160 else "CRITICAL",
                    title=f"Temperatura elevada en {sensor.position}",
                    message=f"La llanta {sensor.position} reporta {reading.temperature_f:.1f} F.",
                    trigger_value=reading.temperature_f,
                    threshold_value=max(target_temperature, 120.0),
                    unit="F",
                )
            )

        if reading.estimated_tread_depth is not None:
            if reading.estimated_tread_depth <= critical_tread:
                alerts.append(
                    AlertEngine.create_alert(
                        truck=truck,
                        sensor=sensor,
                        alert_type="TIRE_WEAR_CRITICAL",
                        severity="CRITICAL",
                        title=f"Desgaste critico en {sensor.position}",
                        message="La profundidad estimada de banda llego a nivel critico.",
                        trigger_value=reading.estimated_tread_depth,
                        threshold_value=critical_tread,
                        unit="32nds",
                    )
                )
            elif reading.estimated_tread_depth <= warning_tread:
                alerts.append(
                    AlertEngine.create_alert(
                        truck=truck,
                        sensor=sensor,
                        alert_type="TIRE_WEAR_WARNING",
                        severity="HIGH",
                        title=f"Desgaste en advertencia para {sensor.position}",
                        message="La profundidad estimada de banda requiere atencion preventiva.",
                        trigger_value=reading.estimated_tread_depth,
                        threshold_value=warning_tread,
                        unit="32nds",
                    )
                )

        if reading.sensor_battery is not None and reading.sensor_battery < 20:
            alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    sensor=sensor,
                    alert_type="LOW_BATTERY_SENSOR",
                    severity="MEDIUM",
                    title=f"Bateria baja en sensor {sensor.position}",
                    message="El sensor de llanta requiere mantenimiento preventivo.",
                    trigger_value=reading.sensor_battery,
                    threshold_value=20.0,
                    unit="%",
                )
            )

        return alerts

    @staticmethod
    def check_hos_alerts(driver):
        HOSCalculator.update_hos_status(driver)
        hos_alerts = HOSCalculator.generate_hos_alerts(driver)
        truck = (
            driver.trips.select_related("truck").order_by("-scheduled_start").first().truck
            if driver.trips.select_related("truck").exists()
            else None
        )

        system_alerts = []
        if not truck:
            return hos_alerts

        for hos_alert in hos_alerts:
            alert_type = "HOS_VIOLATION" if hos_alert.severity == "VIOLATION" else "HOS_WARNING"
            severity = "CRITICAL" if hos_alert.severity == "VIOLATION" else "HIGH"
            system_alerts.append(
                AlertEngine.create_alert(
                    truck=truck,
                    alert_type=alert_type,
                    severity=severity,
                    title=hos_alert.title,
                    message=hos_alert.message,
                    trigger_value=hos_alert.current_value,
                    threshold_value=hos_alert.threshold_value,
                    unit="hours",
                    location=hos_alert.location,
                )
            )
        return hos_alerts + system_alerts

    @staticmethod
    def check_weight_alerts(truck):
        latest = WeightInspection.objects.filter(truck=truck).order_by("-timestamp").first()
        if not latest or not latest.is_overweight:
            return []

        return [
            AlertEngine.create_alert(
                truck=truck,
                alert_type="OVERWEIGHT_GROSS",
                severity="CRITICAL",
                title=f"Sobrepeso detectado en {truck.plate}",
                message="La ultima inspeccion de peso excede el limite bruto permitido.",
                trigger_value=latest.gross_weight,
                threshold_value=80000.0,
                unit="lbs",
                location=latest.location,
            )
        ]
