from django.db import models
from django.contrib.auth.models import User
from apps.core.models import CarrierCompany
from apps.devices.models import Truck
from apps.hos_monitoring.models import Driver

class FleetManager(models.Model):
    """
    Representa a un despachador o gerente de flota (usuario del sistema).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fleet_manager')
    company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE, related_name='managers')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Gerente de Flota / Despachador"
        verbose_name_plural = "Gerentes de Flota / Despachadores"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.company.legal_name})"


class Trip(models.Model):
    """
    Viaje o despacho asignado a una tractomula y conductor.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_TRANSIT', 'En Tránsito'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado')
    ]
    
    company = models.ForeignKey(CarrierCompany, on_delete=models.CASCADE, related_name='trips', verbose_name="Empresa")
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, related_name='trips', verbose_name="Tractomula")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, related_name='trips', verbose_name="Conductor")
    dispatcher = models.ForeignKey(FleetManager, on_delete=models.SET_NULL, null=True, related_name='dispatched_trips', verbose_name="Despachador")
    
    origin_address = models.CharField(max_length=255, verbose_name="Origen")
    destination_address = models.CharField(max_length=255, verbose_name="Destino")
    
    scheduled_start = models.DateTimeField(verbose_name="Inicio Programado")
    scheduled_end = models.DateTimeField(verbose_name="Fin Estimado")
    
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Real")
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name="Fin Real")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Estado")
    route_data = models.JSONField(null=True, blank=True, verbose_name="Datos de Ruta (JSON)", help_text="Coordenadas y waypoints de la ruta planeada.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Viaje / Despacho"
        verbose_name_plural = "Viajes / Despachos"
        ordering = ['-scheduled_start']

    def __str__(self):
        return f"Viaje {self.id}: {self.origin_address} -> {self.destination_address}"