from django.db import models
from apps.core.models import CarrierCompany

class Truck(models.Model):
    """
    Modelo que representa una tractomula en el sistema.
    """
    vin = models.CharField(max_length=50, unique=True, verbose_name="VIN")
    plate = models.CharField(max_length=20, verbose_name="Placa")
    brand = models.CharField(max_length=50, verbose_name="Marca")
    model = models.CharField(max_length=50, verbose_name="Modelo")
    year = models.IntegerField(verbose_name="Año")
    num_tires = models.IntegerField(default=18, verbose_name="Número de Llantas")
    carrier = models.ForeignKey(CarrierCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name='trucks')
    status = models.CharField(max_length=20, default='ACTIVE', verbose_name="Estado")
    
    # Coordenadas geográficas (última ubicación conocida)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tractomula"
        verbose_name_plural = "Tractomulas"

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"


class MasterDevice(models.Model):
    """
    Dispositivo maestro (en cabina) que recolecta datos de los sensores esclavos.
    """
    device_code = models.CharField(max_length=50, unique=True, verbose_name="Código del Dispositivo")
    truck = models.OneToOneField(Truck, on_delete=models.CASCADE, related_name='master_device', verbose_name="Tractomula Asignada")
    firmware_version = models.CharField(max_length=20, verbose_name="Versión Firmware")
    sim_card = models.CharField(max_length=30, verbose_name="SIM Card (ICCID)")
    battery_level = models.FloatField(default=100.0, verbose_name="Nivel de Batería (%)")
    signal_strength = models.FloatField(default=0.0, verbose_name="Señal (dBm)")
    status = models.CharField(max_length=20, default='ONLINE', verbose_name="Estado")
    last_ping = models.DateTimeField(null=True, blank=True, verbose_name="Última Conexión")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dispositivo Maestro"
        verbose_name_plural = "Dispositivos Maestros"

    def __str__(self):
        return f"Master: {self.device_code} ({self.truck.plate})"


class TireSensor(models.Model):
    """
    Sensor esclavo individual por llanta.
    """
    POSITION_CHOICES = [(f"{ax}-{i}", f"{ax}-{i}") for ax in ['FL','FR','RL','RR','TL','TR'] for i in range(1, 5)]
    
    sensor_code = models.CharField(max_length=50, unique=True, verbose_name="Código del Sensor")
    master_device = models.ForeignKey(MasterDevice, on_delete=models.CASCADE, related_name='tire_sensors', verbose_name="Dispositivo Maestro")
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, verbose_name="Posición (Eje)")
    tire_brand = models.CharField(max_length=50, verbose_name="Marca de Llanta")
    install_date = models.DateField(verbose_name="Fecha de Instalación")
    lifecycle_km = models.FloatField(default=200000.0, verbose_name="Ciclo de Vida Estimado (km/millas)")
    accumulated_km = models.FloatField(default=0.0, verbose_name="Recorrido Acumulado")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sensor de Llanta"
        verbose_name_plural = "Sensores de Llantas"
        unique_together = ('master_device', 'position')

    def __str__(self):
        return f"Sensor: {self.sensor_code} - Pos: {self.position}"


class VehicleReading(models.Model):
    """
    Lecturas telemétricas generales del vehículo reportadas por el MasterDevice.
    """
    master_device = models.ForeignKey(MasterDevice, on_delete=models.CASCADE, related_name='vehicle_readings')
    timestamp = models.DateTimeField(verbose_name="Marca de Tiempo")
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    speed_mph = models.FloatField(verbose_name="Velocidad (mph)")
    heading = models.FloatField(verbose_name="Rumbo (grados)")
    
    # Datos OBD-II (Opcionales)
    obd_rpm = models.FloatField(null=True, blank=True, verbose_name="RPM")
    obd_fuel_level = models.FloatField(null=True, blank=True, verbose_name="Nivel Combustible (%)")
    
    # Acelerómetro
    accel_x = models.FloatField(null=True, blank=True)
    accel_y = models.FloatField(null=True, blank=True)
    accel_z = models.FloatField(null=True, blank=True)
    
    battery_voltage = models.FloatField(null=True, blank=True, verbose_name="Voltaje Batería (V)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lectura de Vehículo"
        verbose_name_plural = "Lecturas de Vehículos"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Lectura {self.master_device.truck.plate} - {self.timestamp}"