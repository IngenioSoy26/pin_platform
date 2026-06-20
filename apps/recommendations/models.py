from django.db import models
from apps.devices.models import Truck
from apps.alerts.models import Alert

class Recommendation(models.Model):
    REC_TYPES = [
        ('TIRE_SHOP', 'Tienda de Llantas'),
        ('REST_STOP', 'Parada de Descanso'),
        ('RESTAURANT', 'Restaurante'),
        ('FUEL_STATION', 'Estación de Combustible'),
        ('ALT_FUEL', 'Combustible Alternativo'),
        ('RECYCLING_CENTER', 'Centro de Reciclaje'),
        ('WIM_STATION', 'Estación WIM'),
        ('HOTEL', 'Hotel'),
        ('MECHANIC', 'Mecánico'),
    ]
    STATUS_CHOICES = [
        ('GENERATED', 'Generada'),
        ('SENT', 'Enviada al Conductor'),
        ('ACCEPTED', 'Aceptada'),
        ('REJECTED', 'Rechazada'),
        ('COMPLETED', 'Completada'),
    ]

    alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendations')
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='recommendations')
    rec_type = models.CharField(max_length=20, choices=REC_TYPES)
    priority = models.IntegerField(default=5) # 1-10
    
    target_name = models.CharField(max_length=255)
    target_address = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    distance_km = models.FloatField(null=True, blank=True)
    estimated_time_min = models.IntegerField(null=True, blank=True)
    estimated_cost_usd = models.FloatField(null=True, blank=True)
    
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='GENERATED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recomendación: {self.get_rec_type_display()} para {self.truck.plate}"
