import os

base_dir = r"c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\apps"

code_templates = {
    "stations": {
        "admin.py": """from django.contrib import admin
from .models import TruckStation, TruckStopParking

@admin.register(TruckStation)
class TruckStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'operator', 'has_tires', 'has_mechanic', 'has_parking')
    search_fields = ('name', 'operator')
    list_filter = ('has_tires', 'has_mechanic', 'has_diesel')

    def has_parking(self, obj):
        return obj.parking_spaces > 0
    has_parking.boolean = True

@admin.register(TruckStopParking)
class TruckStopParkingAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'total_spots')
    search_fields = ('name',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import TruckStation, TruckStopParking

class TruckStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckStation
        fields = '__all__'

class TruckStopParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckStopParking
        fields = '__all__'
""",
        "services.py": """import math
from .models import TruckStation

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Radio de la Tierra en km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class StationRecommenderService:
    @staticmethod
    def find_nearby_stations(lat, lon, radius_km=50, needs_tires=False, needs_parking=False):
        \"\"\"
        Busca estaciones cercanas. Crucial para emergencias de llantas o descanso (HOS).
        \"\"\"
        # Bounding box aproximado (1 grado latitud ~ 111 km)
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        qs = TruckStation.objects.filter(
            latitude__gte=lat - delta_lat, latitude__lte=lat + delta_lat,
            longitude__gte=lon - delta_lon, longitude__lte=lon + delta_lon
        )
        
        if needs_tires:
            qs = qs.filter(has_tires=True)
        if needs_parking:
            qs = qs.filter(parking_spaces__gt=0)
            
        results = []
        for station in qs:
            if station.latitude and station.longitude:
                dist = haversine(lat, lon, station.latitude, station.longitude)
                if dist <= radius_km:
                    results.append({'station': station, 'distance_km': dist})
                    
        return sorted(results, key=lambda x: x['distance_km'])
"""
    },
    "fuel_alternative": {
        "admin.py": """from django.contrib import admin
from .models import AlternativeFuelStation

@admin.register(AlternativeFuelStation)
class AlternativeFuelStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'fuel_type', 'is_hd_fuel')
    list_filter = ('fuel_type', 'is_hd_fuel')
    search_fields = ('name',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import AlternativeFuelStation

class AlternativeFuelStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternativeFuelStation
        fields = '__all__'
""",
        "services.py": """import math
from .models import AlternativeFuelStation

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

class FuelRecommenderService:
    @staticmethod
    def find_nearby_hd_fuel(lat, lon, radius_km=100):
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        qs = AlternativeFuelStation.objects.filter(
            is_hd_fuel=True,
            latitude__gte=lat - delta_lat, latitude__lte=lat + delta_lat,
            longitude__gte=lon - delta_lon, longitude__lte=lon + delta_lon
        )
        
        results = []
        for station in qs:
            if station.latitude and station.longitude:
                dist = haversine(lat, lon, station.latitude, station.longitude)
                if dist <= radius_km:
                    results.append({'station': station, 'distance_km': dist})
        return sorted(results, key=lambda x: x['distance_km'])
"""
    },
    "recycling": {
        "admin.py": """from django.contrib import admin
from .models import RecyclingCenter

@admin.register(RecyclingCenter)
class RecyclingCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'recycling_type', 'accepts_tires', 'capacity_tons')
    list_filter = ('accepts_tires',)
    search_fields = ('name',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import RecyclingCenter

class RecyclingCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecyclingCenter
        fields = '__all__'
""",
        "services.py": """import math
from .models import RecyclingCenter

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

class RecyclingRecommenderService:
    @staticmethod
    def find_tire_recycling(lat, lon, radius_km=150):
        \"\"\"Busca centros de reciclaje de llantas (Economía Circular).\"\"\"
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        qs = RecyclingCenter.objects.filter(
            accepts_tires=True,
            latitude__gte=lat - delta_lat, latitude__lte=lat + delta_lat,
            longitude__gte=lon - delta_lon, longitude__lte=lon + delta_lon
        )
        
        results = []
        for center in qs:
            if center.latitude and center.longitude:
                dist = haversine(lat, lon, center.latitude, center.longitude)
                if dist <= radius_km:
                    results.append({'center': center, 'distance_km': dist})
        return sorted(results, key=lambda x: x['distance_km'])
"""
    },
    "regulation": {
        "admin.py": """from django.contrib import admin
from .models import WIMStation, SizeWeightRegulation

@admin.register(WIMStation)
class WIMStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'station_code', 'direction')
    search_fields = ('name', 'station_code')

@admin.register(SizeWeightRegulation)
class SizeWeightRegulationAdmin(admin.ModelAdmin):
    list_display = ('state', 'max_weight_lbs', 'max_length_ft')
    search_fields = ('state',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import WIMStation, SizeWeightRegulation

class WIMStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WIMStation
        fields = '__all__'

class SizeWeightRegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeWeightRegulation
        fields = '__all__'
""",
        "services.py": """from .models import SizeWeightRegulation

class RegulationService:
    @staticmethod
    def get_state_limits(state_code):
        return SizeWeightRegulation.objects.filter(state=state_code).first()
"""
    },
    "routes": {
        "admin.py": """from django.contrib import admin
from .models import HighwayRoute

@admin.register(HighwayRoute)
class HighwayRouteAdmin(admin.ModelAdmin):
    list_display = ('route_id', 'route_name', 'state', 'length_km')
    search_fields = ('route_name', 'route_id', 'state')
    list_filter = ('state',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import HighwayRoute

class HighwayRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighwayRoute
        fields = '__all__'
""",
        "services.py": """from .models import HighwayRoute

class RouteService:
    @staticmethod
    def get_routes_by_state(state_code):
        return HighwayRoute.objects.filter(state=state_code)
"""
    },
    "carriers": {
        "admin.py": """from django.contrib import admin
from .models import Carrier, MonthlyTransportIndicator

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'dot_number', 'num_power_units', 'state')
    search_fields = ('legal_name', 'dot_number')
    list_filter = ('state',)

@admin.register(MonthlyTransportIndicator)
class MonthlyTransportIndicatorAdmin(admin.ModelAdmin):
    list_display = ('indicator_name', 'date', 'value', 'unit')
    search_fields = ('indicator_name',)
    list_filter = ('date',)
""",
        "serializers.py": """from rest_framework import serializers
from .models import Carrier, MonthlyTransportIndicator

class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = '__all__'
""",
        "services.py": """from .models import Carrier

class CarrierService:
    @staticmethod
    def get_top_carriers(limit=10):
        return Carrier.objects.order_by('-num_power_units')[:limit]
"""
    }
}

for app, files in code_templates.items():
    app_dir = os.path.join(base_dir, app)
    for filename, content in files.items():
        with open(os.path.join(app_dir, filename), "w", encoding='utf-8') as f:
            f.write(content)

print("Phase 7 files populated with business logic.")
