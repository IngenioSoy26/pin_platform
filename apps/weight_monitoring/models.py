from django.db import models
from apps.devices.models import Truck

class WeightRegulation(models.Model):
    """
    Límites de peso legales según la Federal Bridge Formula y variaciones estatales.
    """
    state = models.CharField(max_length=2, unique=True, verbose_name="Código de Estado (Ej: TX)")
    state_name = models.CharField(max_length=100, verbose_name="Nombre del Estado")
    
    # Límites Base (Federales por defecto)
    federal_gross_limit = models.FloatField(default=80000.0, verbose_name="Límite Bruto Federal (lbs)")
    state_gross_limit = models.FloatField(default=80000.0, verbose_name="Límite Bruto Estatal (lbs)")
    single_axle_limit = models.FloatField(default=20000.0, verbose_name="Límite Eje Simple (lbs)")
    tandem_axle_limit = models.FloatField(default=34000.0, verbose_name="Límite Eje Tándem (lbs)")
    
    # Impacto en llantas
    weight_wear_factor = models.FloatField(default=1.0, verbose_name="Factor Base de Desgaste por Peso")
    permits_available = models.BooleanField(default=False, verbose_name="Permite Permisos de Exceso")

    class Meta:
        verbose_name = "Regulación de Peso"
        verbose_name_plural = "Regulaciones de Peso"

    def __str__(self):
        return f"Regulación de Peso - {self.state_name}"


class AxleConfiguration(models.Model):
    """
    Configuración de ejes para una tractomula específica, necesaria para la Federal Bridge Formula.
    """
    AXLE_TYPES = [
        ('STEER', 'Eje de Dirección (Frontal)'),
        ('SINGLE', 'Eje Simple'),
        ('TANDEM', 'Eje Tándem'),
        ('TRIDEM', 'Eje Trídem')
    ]
    
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='axles')
    axle_number = models.IntegerField(verbose_name="Número de Eje (De frente a atrás)")
    axle_type = models.CharField(max_length=10, choices=AXLE_TYPES, verbose_name="Tipo de Eje")
    position_ft = models.FloatField(verbose_name="Distancia desde el frente (Pies)")
    tire_count = models.IntegerField(default=4, verbose_name="Número de Llantas en el Eje")
    
    # Pesos
    max_weight_capacity = models.FloatField(verbose_name="Capacidad Máxima Física (lbs)")
    current_weight = models.FloatField(default=0.0, verbose_name="Peso Actual Estimado (lbs)")

    class Meta:
        verbose_name = "Configuración de Eje"
        verbose_name_plural = "Configuraciones de Ejes"
        ordering = ['truck', 'axle_number']

    def __str__(self):
        return f"{self.truck.plate} - Eje {self.axle_number} ({self.axle_type})"


class WeightInspection(models.Model):
    """
    Registro de una inspección de peso, ya sea por una estación WIM o pesaje estático.
    """
    INSPECTION_TYPES = [
        ('WIM', 'Weigh-In-Motion (Dinámico)'),
        ('STATIC', 'Estación de Pesaje (Estático)'),
        ('ESTIMATED', 'Estimado por Sensores IoT')
    ]
    
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='weight_inspections')
    timestamp = models.DateTimeField(verbose_name="Fecha y Hora")
    location = models.CharField(max_length=255, verbose_name="Ubicación de la Inspección")
    state = models.ForeignKey(WeightRegulation, on_delete=models.SET_NULL, null=True, blank=True)
    inspection_type = models.CharField(max_length=15, choices=INSPECTION_TYPES)
    
    # Pesos registrados
    gross_weight = models.FloatField(verbose_name="Peso Bruto Registrado (lbs)")
    axle_weights = models.JSONField(verbose_name="Pesos por Eje (JSON)")
    
    # Resultados
    is_overweight = models.BooleanField(default=False, verbose_name="¿Exceso de Peso?")
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inspección de Peso"
        verbose_name_plural = "Inspecciones de Peso"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Pesaje {self.truck.plate} - {self.gross_weight} lbs ({self.timestamp.date()})"