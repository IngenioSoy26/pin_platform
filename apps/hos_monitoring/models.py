from django.db import models
from apps.devices.models import Truck

class Driver(models.Model):
    """
    Representa a un conductor sujeto a las regulaciones FMCSA.
    """
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    license_number = models.CharField(max_length=50, unique=True, verbose_name="Número de Licencia (CDL)")
    license_state = models.CharField(max_length=2, verbose_name="Estado Emisor")
    cdl_class = models.CharField(max_length=1, default='A', verbose_name="Clase CDL")
    hire_date = models.DateField(verbose_name="Fecha de Contratación")
    status = models.CharField(max_length=20, default='ACTIVE', choices=[('ACTIVE', 'Activo'), ('INACTIVE', 'Inactivo'), ('SUSPENDED', 'Suspendido')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"

    def __str__(self):
        return f"{self.first_name} {self.last_name} (CDL: {self.license_number})"


class DriverLog(models.Model):
    """
    Registro electrónico de estado del conductor (ELD Log).
    """
    STATUS_CHOICES = [
        ('DRIVING', 'Driving'),
        ('ON_DUTY', 'On-Duty (Not Driving)'),
        ('OFF_DUTY', 'Off-Duty'),
        ('SLEEPER', 'Sleeper Berth')
    ]
    
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='logs')
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(verbose_name="Marca de Tiempo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Estado de Servicio")
    location = models.CharField(max_length=255, verbose_name="Ubicación Registrada")
    odometer = models.FloatField(verbose_name="Odómetro (Millas)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Conductor (ELD)"
        verbose_name_plural = "Registros de Conductores (ELD)"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.driver} - {self.status} @ {self.timestamp}"


class HOSCompliance(models.Model):
    """
    Estado actual de cumplimiento de Horas de Servicio de un conductor.
    Actualizado dinámicamente con cada nuevo DriverLog.
    """
    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, related_name='hos_compliance')
    cycle_start = models.DateTimeField(verbose_name="Inicio del Ciclo de 7/8 días")
    cycle_type = models.CharField(max_length=20, choices=[('60_7', '60 horas en 7 días'), ('70_8', '70 horas en 8 días')], default='70_8')
    
    # Acumuladores de tiempo (en minutos para mayor precisión)
    driving_time_today = models.IntegerField(default=0, verbose_name="Tiempo de Conducción Hoy (min)")
    on_duty_time_today = models.IntegerField(default=0, verbose_name="Tiempo On-Duty Hoy (min)")
    consecutive_driving_time = models.IntegerField(default=0, verbose_name="Tiempo de Conducción Consecutiva (min)")
    
    hours_7days = models.IntegerField(default=0, verbose_name="Horas On-Duty 7 Días (min)")
    hours_8days = models.IntegerField(default=0, verbose_name="Horas On-Duty 8 Días (min)")
    
    # Marcas de tiempo importantes
    last_10h_off = models.DateTimeField(null=True, blank=True, verbose_name="Último Descanso 10h")
    last_30min_break = models.DateTimeField(null=True, blank=True, verbose_name="Último Descanso 30min")
    
    # Excepciones
    is_short_haul = models.BooleanField(default=False, verbose_name="Excepción Short-Haul (150 millas)")
    adverse_conditions = models.BooleanField(default=False, verbose_name="Condiciones Adversas (+2h)")
    
    # Estado global
    is_compliant = models.BooleanField(default=True, verbose_name="En Cumplimiento")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cumplimiento HOS"
        verbose_name_plural = "Cumplimientos HOS"

    def __str__(self):
        return f"HOS Status - {self.driver}"


class HOSAlert(models.Model):
    """
    Alertas generadas por posibles violaciones a las reglas FMCSA.
    """
    ALERT_TYPES = [
        ('VIOLATION_11H', 'Violación: Límite de 11h de Conducción'),
        ('VIOLATION_14H', 'Violación: Límite de 14h On-Duty'),
        ('VIOLATION_30M', 'Violación: Falta de Pausa de 30 minutos'),
        ('VIOLATION_60_70H', 'Violación: Límite de Ciclo 60/70 horas'),
        ('WARNING_11H', 'Advertencia: Cerca del Límite de 11h'),
        ('WARNING_14H', 'Advertencia: Cerca del Límite de 14h'),
        ('WARNING_30M', 'Advertencia: Pausa de 30 min inminente'),
        ('WARNING_60_70H', 'Advertencia: Cerca del Límite de Ciclo')
    ]
    
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='hos_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Tipo de Alerta")
    severity = models.CharField(max_length=10, choices=[('WARNING', 'Advertencia'), ('VIOLATION', 'Violación Crítica')])
    title = models.CharField(max_length=150)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    
    current_value = models.FloatField(verbose_name="Valor Actual (Horas)", null=True, blank=True)
    threshold_value = models.FloatField(verbose_name="Límite Permitido (Horas)", null=True, blank=True)
    
    status = models.CharField(max_length=20, default='ACTIVE', choices=[('ACTIVE', 'Activa'), ('ACKNOWLEDGED', 'Reconocida'), ('RESOLVED', 'Resuelta')])

    class Meta:
        verbose_name = "Alerta HOS"
        verbose_name_plural = "Alertas HOS"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.driver} - {self.title}"