from django.db import models

class Amenity(models.Model):
    """
    Modelo dinámico para clasificar servicios y amenidades disponibles en cualquier locación.
    Ej: 'Duchas', 'Restaurante', 'Taller de Llantas', 'Venta de Llantas', 'Báscula', etc.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de Amenidad")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Categoría", help_text="Ej: Alimentación, Mantenimiento, Descanso")

    class Meta:
        verbose_name = "Amenity / Service"
        verbose_name_plural = "Amenities / Services"
        ordering = ['name']

    def __str__(self):
        return self.name

class CarrierCompany(models.Model):
    """
    Datos de empresas transportistas (Company_Census_File_20260604.csv).
    """
    dot_number = models.CharField(max_length=50, unique=True, verbose_name="DOT Number")
    legal_name = models.CharField(max_length=255, verbose_name="Legal Name")
    dba_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="DBA Name")
    carrier_operation = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.legal_name} (DOT: {self.dot_number})"

class Location(models.Model):
    """
    Modelo base para cualquier punto geográfico en la plataforma.
    Usamos DecimalField para soportar lat/lon sin depender de GDAL/PostGIS en Windows,
    pero preparado para migrar a PointField de PostGIS si se requiere después.
    """
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Datos de Contacto y Operación
    operator = models.CharField(max_length=255, default='Sin Información')
    phone = models.CharField(max_length=50, default='Sin Información')
    website = models.URLField(max_length=500, blank=True, null=True)
    
    # Coordenadas geográficas estándar
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Relación dinámica para asignar múltiples servicios a un punto
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='locations', verbose_name="Servicios y Amenidades")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

class TruckStop(Location):
    """
    Estaciones de descanso y servicio (NTAD_Truck_Stop_Parking).
    Hereda de Location. Las amenidades (duchas, reparación, etc.) se gestionan en el ManyToManyField 'amenities'.
    """
    facility_type = models.CharField(max_length=100, blank=True, null=True)
    parking_spaces = models.IntegerField(default=0)
    diesel_lanes = models.IntegerField(default=0, verbose_name="Islas Diésel Tractomulas")

    class Meta:
        verbose_name = "Truck Stop"
        verbose_name_plural = "Truck Stops"

class WIMStation(Location):
    """
    Estaciones de pesaje en movimiento (NTAD_Weigh_in_Motion_Stations).
    Hereda de Location.
    """
    station_id = models.CharField(max_length=50, unique=True)
    direction_of_travel = models.CharField(max_length=10, blank=True, null=True)
    number_of_lanes = models.IntegerField(default=1)
    status = models.CharField(max_length=50, default="Operational")

    class Meta:
        verbose_name = "WIM Station"
        verbose_name_plural = "WIM Stations"

class AlternativeFuelStation(Location):
    """
    Estaciones de combustible alternativo (alt_fuel_stations).
    Hereda de Location.
    """
    fuel_type_code = models.CharField(max_length=20) # ELEC, CNG, LNG, etc.
    ev_connector_types = models.CharField(max_length=255, blank=True, null=True) # Para estaciones eléctricas
    is_public = models.BooleanField(default=True)
    maximum_vehicle_class = models.CharField(max_length=50, blank=True, null=True, verbose_name="Clase Máxima de Vehículo")
    cng_dispenser_num = models.IntegerField(default=0, verbose_name="Número de Islas CNG")
    ev_dc_fast_count = models.IntegerField(default=0, verbose_name="Número de Islas EV Rápidas")

    class Meta:
        verbose_name = "Alternative Fuel Station"
        verbose_name_plural = "Alternative Fuel Stations"

class TireShop(Location):
    """
    Talleres de llantas para camiones pesados (tire_shops_usa_osm).
    Hereda de Location.
    """
    brand = models.CharField(max_length=100, blank=True, null=True)
    is_24_hours = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tire Shop"
        verbose_name_plural = "Tire Shops"

class RecyclingFacility(Location):
    """
    Infraestructura de reciclaje, útil para temas de llantas usadas o chatarra.
    (US_Recycling_Infrastructure_2022)
    Hereda de Location.
    """
    population_served = models.IntegerField(default=0, blank=True, null=True)
    tires_recycled_tons = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    tires_generated_tons = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "Recycling Facility"
        verbose_name_plural = "Recycling Facilities"

class TransportationStatistic(models.Model):
    """
    Datos mensuales macroeconómicos del sector (Monthly_Transportation_Statistics).
    No hereda de Location porque son datos de tiempo, no de espacio.
    """
    date = models.DateField(unique=True)
    highway_fatalities = models.IntegerField(blank=True, null=True)
    truck_employment = models.IntegerField(blank=True, null=True) # Transportation Employment - Truck Transportation
    truck_tonnage_index = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    diesel_price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True) # Highway Fuel Price - On-highway Diesel
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transportation Statistic"
        verbose_name_plural = "Transportation Statistics"
        ordering = ['-date']

    def __str__(self):
        return f"Stats for {self.date.strftime('%B %Y')}"

class WeightEnforcementStatistic(models.Model):
    """
    Datos anuales por estado de pesaje de camiones e infracciones (Truck_Size_and_Weight_Enforcement_Data).
    Útil para el Dashboard Gerencial (Identificar estados con más controles/multas).
    """
    year = models.IntegerField(verbose_name="Año")
    state = models.CharField(max_length=10, verbose_name="Estado")
    vehicles_weighed_fixed = models.BigIntegerField(default=0, verbose_name="Pesados (Báscula Fija)")
    vehicles_weighed_wim = models.BigIntegerField(default=0, verbose_name="Pesados (WIM en movimiento)")
    oversize_violations = models.IntegerField(default=0, verbose_name="Multas por Tamaño")
    overweight_violations = models.IntegerField(default=0, verbose_name="Multas por Peso")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Weight Enforcement Stat"
        verbose_name_plural = "Weight Enforcement Stats"
        unique_together = ('year', 'state')
        ordering = ['-year', 'state']

    def __str__(self):
        return f"{self.state} ({self.year}) - Enforcement"
