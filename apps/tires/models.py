from django.db import models
from apps.devices.models import TireSensor

class TirePositionConfig(models.Model):
    """
    Configuración de parámetros ideales por posición y tipo de eje.
    """
    position = models.CharField(max_length=10, unique=True, verbose_name="Posición (Ej: FL-1)")
    axle_type = models.CharField(max_length=20, choices=[('STEER', 'Steer'), ('DRIVE', 'Drive'), ('TRAILER', 'Trailer')], verbose_name="Tipo de Eje")
    
    # Profundidad de banda (FMCSA)
    new_tread_depth = models.FloatField(help_text="En 32nds de pulgada", verbose_name="Profundidad Nueva")
    warning_tread_depth = models.FloatField(verbose_name="Profundidad Advertencia")
    critical_tread_depth = models.FloatField(verbose_name="Profundidad Crítica (Legal)")
    
    # Parámetros físicos ideales
    target_pressure = models.FloatField(verbose_name="Presión Ideal (PSI)")
    target_temperature = models.FloatField(verbose_name="Temperatura Ideal (°F)")
    max_load = models.FloatField(verbose_name="Carga Máxima (lbs)")
    
    # Parámetros predictivos base
    base_lifecycle_miles = models.FloatField(verbose_name="Ciclo Base (millas)")
    base_wear_rate = models.FloatField(verbose_name="Tasa de Desgaste Base (32nds / 1000 mi)")

    class Meta:
        verbose_name = "Configuración de Posición"
        verbose_name_plural = "Configuraciones de Posición"

    def __str__(self):
        return f"{self.position} ({self.axle_type})"


class TireReading(models.Model):
    """
    Lecturas específicas de cada llanta.
    """
    sensor = models.ForeignKey(TireSensor, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField()
    
    pressure_psi = models.FloatField(verbose_name="Presión (PSI)")
    temperature_f = models.FloatField(verbose_name="Temperatura (°F)")
    vibration_g = models.FloatField(verbose_name="Vibración (G)")
    
    estimated_tread_depth = models.FloatField(null=True, blank=True, verbose_name="Profundidad Estimada (32nds)")
    rssi = models.FloatField(null=True, blank=True, verbose_name="Fuerza de Señal BT")
    sensor_battery = models.FloatField(null=True, blank=True, verbose_name="Batería Sensor (%)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lectura de Llanta"
        verbose_name_plural = "Lecturas de Llantas"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Lectura {self.sensor.sensor_code} - {self.timestamp}"


class TireMaintenanceLog(models.Model):
    """
    Registro de mantenimientos realizados a una llanta.
    """
    sensor = models.ForeignKey(TireSensor, on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_type = models.CharField(max_length=50, verbose_name="Tipo de Mantenimiento")
    timestamp = models.DateTimeField(verbose_name="Fecha/Hora")
    mileage = models.FloatField(verbose_name="Millaje al Mantenimiento")
    
    tread_before = models.FloatField(null=True, blank=True, verbose_name="Profundidad Antes (32nds)")
    tread_after = models.FloatField(null=True, blank=True, verbose_name="Profundidad Después (32nds)")
    
    notes = models.TextField(null=True, blank=True, verbose_name="Notas")
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo (USD)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Mantenimiento"
        verbose_name_plural = "Registros de Mantenimiento"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.maintenance_type} - {self.sensor.sensor_code}"