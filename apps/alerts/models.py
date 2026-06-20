from django.db import models
from apps.devices.models import Truck, TireSensor

class Alert(models.Model):
    ALERT_TYPES = [
        ('LOW_PRESSURE', 'Presión Baja'),
        ('HIGH_PRESSURE', 'Presión Alta'),
        ('HIGH_TEMPERATURE', 'Temperatura Alta'),
        ('PUNCTURE', 'Pinchazo'),
        ('TIRE_WEAR_WARNING', 'Advertencia Desgaste'),
        ('TIRE_WEAR_CRITICAL', 'Desgaste Crítico'),
        ('SENSOR_OFFLINE', 'Sensor Desconectado'),
        ('LOW_BATTERY_SENSOR', 'Batería Baja (Sensor)'),
        ('LOW_BATTERY_MASTER', 'Batería Baja (Maestro)'),
        ('HARD_BRAKING', 'Frenazo Brusco'),
        ('HARD_ACCELERATION', 'Aceleración Brusca'),
        ('HOS_WARNING', 'Advertencia HOS'),
        ('HOS_VIOLATION', 'Violación HOS'),
        ('OVERWEIGHT_AXLE', 'Exceso Peso Eje'),
        ('OVERWEIGHT_GROSS', 'Exceso Peso Bruto'),
    ]
    SEVERITY_CHOICES = [
        ('INFO', 'Información'),
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Activa'),
        ('ACKNOWLEDGED', 'Reconocida'),
        ('RESOLVED', 'Resuelta'),
    ]

    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='system_alerts')
    sensor = models.ForeignKey(TireSensor, on_delete=models.SET_NULL, null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=15, choices=SEVERITY_CHOICES)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    trigger_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    
    location = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.truck.plate}"
