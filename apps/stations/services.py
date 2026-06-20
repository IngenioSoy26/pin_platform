import math
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
        """
        Busca estaciones cercanas. Crucial para emergencias de llantas o descanso (HOS).
        """
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
