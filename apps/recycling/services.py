import math
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
        """Busca centros de reciclaje de llantas (Economía Circular)."""
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
