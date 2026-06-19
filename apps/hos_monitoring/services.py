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
        # TODO: Implementar la lógica completa de suma de minutos iterando sobre los logs del día.
        # Por ahora, simplemente validamos el cumplimiento con los datos actuales.
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
            alerts.append(HOSAlert.objects.create(
                driver=driver,
                alert_type='VIOLATION_11H',
                severity='VIOLATION',
                title="Límite de 11 Horas Excedido",
                message="El conductor ha superado el tiempo máximo de conducción permitido.",
                current_value=compliance.driving_time_today / 60.0,
                threshold_value=max_driving_mins / 60.0
            ))
        elif (max_driving_mins - compliance.driving_time_today) <= fmcsa_rules.WARNING_THRESHOLD_MINUTES:
            alerts.append(HOSAlert.objects.create(
                driver=driver,
                alert_type='WARNING_11H',
                severity='WARNING',
                title="Aviso: Límite de 11 Horas Próximo",
                message="Queda menos de 1 hora de tiempo de conducción permitido.",
                current_value=compliance.driving_time_today / 60.0,
                threshold_value=max_driving_mins / 60.0
            ))
            
        return alerts