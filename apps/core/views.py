import json
from django.shortcuts import render
from django.http import JsonResponse
from apps.core.models import TruckStop, WIMStation, TireShop, AlternativeFuelStation, RecyclingFacility
from apps.data_ingestion.models import DatasetUpload

def api_routes(request):
    """
    Retorna la URL del archivo GeoJSON más reciente del Sistema Nacional de Autopistas (NHS).
    """
    dataset = DatasetUpload.objects.filter(dataset_type='ROUTES_NHS', status='COMPLETED').order_by('-uploaded_at').first()
    
    if dataset and dataset.file:
        return JsonResponse({'url': dataset.file.url})
    return JsonResponse({'url': None}, status=404)

def map_view(request):
    """Renderiza la plantilla principal del mapa interactivo."""
    return render(request, "map.html")

def api_locations(request):
    """
    Endpoint que retorna las locaciones filtradas por tipo.
    Optimizado para enviar solo los datos necesarios al mapa de Leaflet.
    """
    layer_type = request.GET.get('type', 'truck_stops')
    
    data = []
    
    if layer_type == 'truck_stops':
        # Optimización con prefetch_related para amenidades
        stops = TruckStop.objects.prefetch_related('amenities').all()
        for s in stops:
            # Enviar None explícitamente en lugar de 0 si no hay información
            parking = s.parking_spaces if s.parking_spaces and s.parking_spaces > 0 else None
            diesel = s.diesel_lanes if s.diesel_lanes and s.diesel_lanes > 0 else None
            
            # Extraer nombres de las amenidades
            amenity_names = [a.name for a in s.amenities.all()]
            data.append({
                'id': s.id,
                'type': 'truck_stop',
                'lat': float(s.latitude) if s.latitude else None,
                'lon': float(s.longitude) if s.longitude else None,
                'name': s.name,
                'operator': s.operator,
                'parking': parking,
                'diesel': diesel,
                'city': s.city or 'No Registrada',
                'state': s.state or 'NA',
                'amenities': amenity_names
            })
            
    elif layer_type == 'wim':
        wims = WIMStation.objects.all().values('id', 'name', 'latitude', 'longitude', 'status')
        for w in wims:
            data.append({
                'id': w['id'],
                'type': 'wim',
                'lat': float(w['latitude']) if w['latitude'] else None,
                'lon': float(w['longitude']) if w['longitude'] else None,
                'name': w['name'],
                'status': w['status']
            })
            
    elif layer_type == 'tires':
        tires = TireShop.objects.all().values('id', 'name', 'latitude', 'longitude', 'is_24_hours')
        for t in tires:
            data.append({
                'id': t['id'],
                'type': 'tire_shop',
                'lat': float(t['latitude']) if t['latitude'] else None,
                'lon': float(t['longitude']) if t['longitude'] else None,
                'name': t['name'],
                'is_24_hours': t['is_24_hours']
            })
            
    elif layer_type == 'alt_fuel':
        # Filtramos para enviar solo las estaciones Heavy Duty (HD / Clase 8)
        fuels = AlternativeFuelStation.objects.filter(maximum_vehicle_class__in=['HD', 'HEAVY-DUTY', 'HEAVY', 'CLASS 8']).prefetch_related('amenities').all()
        for f in fuels:
            amenity_names = [a.name for a in f.amenities.all()]
            data.append({
                'id': f.id,
                'type': 'alt_fuel',
                'lat': float(f.latitude) if f.latitude else None,
                'lon': float(f.longitude) if f.longitude else None,
                'name': f.name,
                'operator': f.operator,
                'city': f.city or 'No Registrada',
                'state': f.state or 'NA',
                'fuel_type': f.fuel_type_code,
                'cng_dispensers': f.cng_dispenser_num,
                'ev_dc_fast': f.ev_dc_fast_count,
                'amenities': amenity_names
            })
            
    elif layer_type == 'recycling':
        recycling = RecyclingFacility.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).values(
            'id', 'name', 'latitude', 'longitude', 'tires_recycled_tons'
        )
        for r in recycling:
            data.append({
                'id': r['id'],
                'type': 'recycling',
                'lat': float(r['latitude']),
                'lon': float(r['longitude']),
                'name': r['name'],
                'tons': float(r['tires_recycled_tons']) if r['tires_recycled_tons'] else 0
            })
            
    # Filtramos locaciones sin coordenadas válidas
    valid_data = [d for d in data if d['lat'] is not None and d['lon'] is not None]
    
    return JsonResponse({'locations': valid_data})