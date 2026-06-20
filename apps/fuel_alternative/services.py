import math
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
