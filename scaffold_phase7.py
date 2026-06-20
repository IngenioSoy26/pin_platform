import os

base_dir = r"c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\apps"

apps_to_create = {
    "stations": {
        "models.py": """from django.db import models

class TruckStation(models.Model):
    name = models.CharField(max_length=255)
    operator = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    
    # Amenities (Cruciales para la toma de decisiones del conductor)
    has_diesel = models.BooleanField(default=False)
    has_def = models.BooleanField(default=False)
    has_restaurant = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_showers = models.BooleanField(default=False)
    has_tires = models.BooleanField(default=False) # Para emergencias de llantas
    has_mechanic = models.BooleanField(default=False)
    
    parking_spaces = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class TruckStopParking(models.Model):
    station = models.ForeignKey(TruckStation, on_delete=models.CASCADE, related_name='parking_details', null=True, blank=True)
    name = models.CharField(max_length=255)
    total_spots = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
""",
    },
    "routes": {
        "models.py": """from django.db import models

class HighwayRoute(models.Model):
    route_id = models.CharField(max_length=100, unique=True)
    route_name = models.CharField(max_length=255)
    route_type = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    length_km = models.FloatField(default=0.0)

    def __str__(self):
        return self.route_name
"""
    },
    "fuel_alternative": {
        "models.py": """from django.db import models

class AlternativeFuelStation(models.Model):
    FUEL_TYPES = [
        ('CNG', 'Compressed Natural Gas'),
        ('LNG', 'Liquefied Natural Gas'),
        ('ELEC', 'Electric'),
        ('H2', 'Hydrogen'),
    ]
    name = models.CharField(max_length=255)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPES)
    is_hd_fuel = models.BooleanField(default=False, verbose_name="Heavy-Duty Ready")
    access_type = models.CharField(max_length=50, null=True, blank=True)
    operators = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.fuel_type})"
"""
    },
    "recycling": {
        "models.py": """from django.db import models

class RecyclingCenter(models.Model):
    name = models.CharField(max_length=255)
    capacity_tons = models.FloatField(null=True, blank=True)
    recycling_type = models.CharField(max_length=100)
    accepts_tires = models.BooleanField(default=False, verbose_name="Acepta Llantas Usadas") # Vital para sostenibilidad PIN
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
"""
    },
    "regulation": {
        "models.py": """from django.db import models

class WIMStation(models.Model):
    name = models.CharField(max_length=255)
    station_code = models.CharField(max_length=50, unique=True)
    direction = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class SizeWeightRegulation(models.Model):
    state = models.CharField(max_length=2, unique=True)
    max_weight_lbs = models.FloatField(default=80000.0)
    max_length_ft = models.FloatField(default=65.0)
    max_width_in = models.FloatField(default=102.0)
    max_height_ft = models.FloatField(default=13.5)

    def __str__(self):
        return f"Regulaciones {self.state}"
"""
    },
    "carriers": {
        "models.py": """from django.db import models

class Carrier(models.Model):
    dot_number = models.CharField(max_length=50, unique=True)
    legal_name = models.CharField(max_length=255)
    dba_name = models.CharField(max_length=255, null=True, blank=True)
    entity_type = models.CharField(max_length=100, null=True, blank=True)
    num_power_units = models.IntegerField(default=0)
    num_drivers = models.IntegerField(default=0)
    state = models.CharField(max_length=2)

    def __str__(self):
        return self.legal_name

class MonthlyTransportIndicator(models.Model):
    date = models.DateField()
    indicator_name = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    region = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.indicator_name} - {self.date}"
"""
    }
}

for app, files in apps_to_create.items():
    app_dir = os.path.join(base_dir, app)
    os.makedirs(app_dir, exist_ok=True)
    
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        pass
        
    with open(os.path.join(app_dir, "apps.py"), "w") as f:
        f.write(f'''from django.apps import AppConfig\n\nclass {app.capitalize().replace('_', '')}Config(AppConfig):\n    default_auto_field = 'django.db.models.BigAutoField'\n    name = 'apps.{app}'\n''')
        
    for filename, content in files.items():
        with open(os.path.join(app_dir, filename), "w", encoding='utf-8') as f:
            f.write(content)
            
    for empty_file in ['admin.py', 'serializers.py', 'views.py', 'urls.py', 'services.py']:
        filepath = os.path.join(app_dir, empty_file)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                if empty_file == 'urls.py':
                    f.write("from django.urls import path\n\nurlpatterns = []\n")
                else:
                    pass

print("Done creating apps")