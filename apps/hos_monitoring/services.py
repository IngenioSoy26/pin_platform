from datetime import timedelta

from django.utils import timezone

from apps.hos_monitoring.models import DriverLog, HOSCompliance, HOSAlert
from apps.hos_monitoring import fmcsa_rules

class HOSCalculator:
    """
    Motor de cálculo para validar el cumplimiento de las regulaciones HOS (FMCSA).
    """
    
    @staticmethod
    def check_compliance(driver):
        """
        Revisa todas las métricas de un conductor y determina si está en violación.
        """
        compliance, created = HOSCompliance.objects.get_or_create(driver=driver, defaults={
            'cycle_start': timezone.now()
        })
        
        is_compliant = True
        
        # Extensión por condiciones adversas
        extension = fmcsa_rules.ADVERSE_CONDITIONS_EXT * 60 if compliance.adverse_conditions else 0
        
        # Regla 1: 11-Hour Driving Limit
        max_driving_mins = (fmcsa_rules.MAX_DRIVING_HOURS * 60) + extension
        if compliance.driving_time_today > max_driving_mins:
            is_compliant = False
            
        # Regla 2: 14-Hour Limit
        max_on_duty_mins = (fmcsa_rules.MAX_ON_DUTY_HOURS * 60) + extension
        if compliance.on_duty_time_today > max_on_duty_mins:
            is_compliant = False
            
        # Regla 3: 30-Minute Break
        if compliance.consecutive_driving_time > (fmcsa_rules.BREAK_REQUIRED_AFTER * 60):
            is_compliant = False
            
        # Regla 4: 60/70-Hour Limit
        limit = fmcsa_rules.CYCLE_70_HOURS_LIMIT if compliance.cycle_type == '70_8' else fmcsa_rules.CYCLE_60_HOURS_LIMIT
        cycle_mins = compliance.hours_8days if compliance.cycle_type == '70_8' else compliance.hours_7days
        if cycle_mins > (limit * 60):
            is_compliant = False

        compliance.is_compliant = is_compliant
        compliance.save()
        
        return is_compliant

    @staticmethod
    def update_hos_status(driver):
        """
        Actualiza los acumuladores de tiempo basado en los últimos registros (Logs).
        Llamado cada vez que ingresa un nuevo DriverLog desde el dispositivo IoT.
        """
        compliance, _ = HOSCompliance.objects.get_or_create(
            driver=driver,
            defaults={"cycle_start": timezone.now()},
        )
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cycle_window = now - timedelta(days=8 if compliance.cycle_type == "70_8" else 7)

        logs_today = list(driver.logs.filter(timestamp__gte=today_start).order_by("timestamp"))
        cycle_logs = list(driver.logs.filter(timestamp__gte=cycle_window).order_by("timestamp"))

        driving_minutes = 0
        on_duty_minutes = 0
        consecutive_driving = 0
        max_consecutive_driving = 0
        last_break = compliance.last_30min_break
        last_10h_off = compliance.last_10h_off

        for current, nxt in zip(logs_today, logs_today[1:]):
            duration_min = max(int((nxt.timestamp - current.timestamp).total_seconds() // 60), 0)
            if current.status == "DRIVING":
                driving_minutes += duration_min
                on_duty_minutes += duration_min
                consecutive_driving += duration_min
                max_consecutive_driving = max(max_consecutive_driving, consecutive_driving)
            elif current.status == "ON_DUTY":
                on_duty_minutes += duration_min
                consecutive_driving = 0
            else:
                if duration_min >= 30:
                    last_break = current.timestamp
                if duration_min >= 600:
                    last_10h_off = current.timestamp
                consecutive_driving = 0

        cycle_minutes = 0
        for current, nxt in zip(cycle_logs, cycle_logs[1:]):
            duration_min = max(int((nxt.timestamp - current.timestamp).total_seconds() // 60), 0)
            if current.status in {"DRIVING", "ON_DUTY"}:
                cycle_minutes += duration_min

        if compliance.cycle_type == "70_8":
            compliance.hours_8days = cycle_minutes
        else:
            compliance.hours_7days = cycle_minutes

        compliance.driving_time_today = driving_minutes
        compliance.on_duty_time_today = on_duty_minutes
        compliance.consecutive_driving_time = max_consecutive_driving
        compliance.last_30min_break = last_break
        compliance.last_10h_off = last_10h_off
        compliance.save()
        HOSCalculator.check_compliance(driver)

    @staticmethod
    def generate_hos_alerts(driver):
        """
        Genera alertas preventivas o de violación basadas en el estado HOS actual.
        """
        compliance = driver.hos_compliance
        extension = fmcsa_rules.ADVERSE_CONDITIONS_EXT * 60 if compliance.adverse_conditions else 0
        
        max_driving_mins = (fmcsa_rules.MAX_DRIVING_HOURS * 60) + extension
        max_on_duty_mins = (fmcsa_rules.MAX_ON_DUTY_HOURS * 60) + extension
        
        alerts = []
        
        # Validación de Conducción (11 horas)
        if compliance.driving_time_today > max_driving_mins:
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='VIOLATION_11H',
                severity='VIOLATION',
                title="Limite de 11 horas excedido",
                message="El conductor supero el tiempo maximo de conduccion permitido.",
                current_value=compliance.driving_time_today / 60.0,
                threshold_value=max_driving_mins / 60.0,
            ))
        elif (max_driving_mins - compliance.driving_time_today) <= fmcsa_rules.WARNING_THRESHOLD_MINUTES:
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='WARNING_11H',
                severity='WARNING',
                title="Aviso: limite de 11 horas proximo",
                message="Queda menos de una hora de tiempo de conduccion permitido.",
                current_value=compliance.driving_time_today / 60.0,
                threshold_value=max_driving_mins / 60.0,
            ))

        if compliance.on_duty_time_today > max_on_duty_mins:
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='VIOLATION_14H',
                severity='VIOLATION',
                title="Limite de 14 horas excedido",
                message="El conductor supero el limite de jornada on-duty.",
                current_value=compliance.on_duty_time_today / 60.0,
                threshold_value=max_on_duty_mins / 60.0,
            ))
        elif (max_on_duty_mins - compliance.on_duty_time_today) <= fmcsa_rules.WARNING_THRESHOLD_MINUTES:
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='WARNING_14H',
                severity='WARNING',
                title="Aviso: limite de 14 horas proximo",
                message="La jornada on-duty esta cerca del limite regulatorio.",
                current_value=compliance.on_duty_time_today / 60.0,
                threshold_value=max_on_duty_mins / 60.0,
            ))

        if compliance.consecutive_driving_time > (fmcsa_rules.BREAK_REQUIRED_AFTER * 60):
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='VIOLATION_30M',
                severity='VIOLATION',
                title="Pausa de 30 minutos incumplida",
                message="El conductor requiere pausa obligatoria de 30 minutos.",
                current_value=compliance.consecutive_driving_time / 60.0,
                threshold_value=fmcsa_rules.BREAK_REQUIRED_AFTER,
            ))

        limit = fmcsa_rules.CYCLE_70_HOURS_LIMIT if compliance.cycle_type == '70_8' else fmcsa_rules.CYCLE_60_HOURS_LIMIT
        cycle_hours = (compliance.hours_8days if compliance.cycle_type == '70_8' else compliance.hours_7days) / 60.0
        if cycle_hours > limit:
            alerts.append(HOSCalculator._get_or_create_alert(
                driver=driver,
                alert_type='VIOLATION_60_70H',
                severity='VIOLATION',
                title="Limite de ciclo excedido",
                message="El conductor supero el acumulado permitido del ciclo HOS.",
                current_value=cycle_hours,
                threshold_value=limit,
            ))

        return alerts

    @staticmethod
    def _get_or_create_alert(driver, alert_type, severity, title, message, current_value, threshold_value):
        active = HOSAlert.objects.filter(
            driver=driver,
            alert_type=alert_type,
            status="ACTIVE",
        ).order_by("-timestamp").first()
        if active:
            return active

        return HOSAlert.objects.create(
            driver=driver,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
        )
