import json
from django.shortcuts import render
from django.http import JsonResponse
from apps.core.models import TruckStop, WIMStation, TireShop, AlternativeFuelStation, RecyclingFacility
from apps.data_ingestion.models import DatasetUpload
from apps.devices.models import Truck
from apps.hos_monitoring.models import HOSAlert
from apps.weight_monitoring.models import WeightInspection

from django.core.management import call_command
import random
from django.utils import timezone
from datetime import timedelta

def simulate_live_tick():
    """Función para mutar aleatoriamente los datos y dar efecto 'En Vivo'."""
    trucks = list(Truck.objects.filter(latitude__isnull=False, longitude__isnull=False))
    if not trucks:
        return
        
    # Simular movimiento físico y telemetría
    for t in trucks:
        # === MOVIMIENTO FÍSICO ===
        if t.status == 'ACTIVE' and t.latitude and t.longitude:
            # Si está activo, moverlo de forma visible en el mapa (aprox 0.1 a 0.3 grados, que es bastante para notarlo)
            lat_move = random.uniform(-0.15, 0.15)
            lon_move = random.uniform(-0.15, 0.15)
            
            # Actualizar coordenadas y guardarlas
            t.latitude = float(t.latitude) + lat_move
            t.longitude = float(t.longitude) + lon_move
        elif t.status == 'MAINTENANCE' and t.latitude and t.longitude:
            # Si está en mantenimiento, se mueve mucho más lento
            lat_move = random.uniform(-0.02, 0.02)
            lon_move = random.uniform(-0.02, 0.02)
            t.latitude = float(t.latitude) + lat_move
            t.longitude = float(t.longitude) + lon_move
        # Si es INACTIVE, no se mueve (0 movimiento)
        
        # 5% de probabilidad de cambiar estado (Sanar o Dañarse)
        if random.random() < 0.05:
            states = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'MAINTENANCE', 'INACTIVE']
            t.status = random.choice(states)
            
        t.save()
        
    # Crear una nueva alerta aleatoria a veces (10% prob)
    if random.random() < 0.1:
        bad_truck = random.choice(trucks)
        
        # 50% HOS Alert, 50% Weight Inspection
        if random.random() > 0.5:
            from apps.hos_monitoring.models import Driver
            driver = Driver.objects.filter(status='ACTIVE').first()
            if driver:
                HOSAlert.objects.create(
                    driver=driver,
                    title="[SIMULADO EN VIVO] Nueva Infracción",
                    alert_type=random.choice(['VIOLATION_11H', 'VIOLATION_14H', 'VIOLATION_60_70H']),
                    severity='VIOLATION',
                    message=f"Alerta generada en tiempo real para {bad_truck.plate}.",
                    current_value=11.5,
                    threshold_value=11.0,
                    status='ACTIVE'
                )
        else:
            WeightInspection.objects.create(
                truck=bad_truck,
                timestamp=timezone.now(),
                location=f"[SIMULADO EN VIVO] Autopista",
                inspection_type='WIM',
                gross_weight=random.uniform(80500.0, 85000.0),
                axle_weights={"steer": 12000, "drive": 34000, "trailer": 38000},
                is_overweight=True
            )

def api_live_dashboard(request):
    """Endpoint AJAX para refrescar los datos del dashboard en tiempo real."""
    simulate_live_tick()
    
    trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    trucks_map_data = []
    
    alert_types = [
        "Pérdida Crítica de Presión (Llanta TR-2)",
        "Temperatura Alta (Eje Trasero)",
        "Alerta HOS: Límite de Ciclo",
        "Exceso de Peso Detectado",
        "Sensor de Llanta Desconectado"
    ]
    
    for t in trucks_qs:
        active_alert = ""
        if t.status == 'MAINTENANCE':
            active_alert = random.choice([alert_types[1], alert_types[4]])
        elif t.status == 'INACTIVE':
            active_alert = random.choice([alert_types[0], alert_types[2], alert_types[3]])
            
        trucks_map_data.append({
            'plate': t.plate,
            'brand': t.brand,
            'status': t.status,
            'lat': float(t.latitude),
            'lon': float(t.longitude),
            'active_alert': active_alert
        })
        
    from django.template.loader import render_to_string
    
    # Renderizar el HTML de alertas actualizadas
    latest_hos = HOSAlert.objects.filter(status='ACTIVE').order_by('-timestamp')[:4]
    latest_weight = WeightInspection.objects.filter(is_overweight=True).order_by('-timestamp')[:4]
    
    # Combinar y ordenar por timestamp
    all_alerts = []
    for h in latest_hos:
        all_alerts.append({'type': 'hos', 'obj': h, 'ts': h.timestamp})
    for w in latest_weight:
        all_alerts.append({'type': 'weight', 'obj': w, 'ts': w.timestamp})
        
    all_alerts.sort(key=lambda x: x['ts'], reverse=True)
    all_alerts = all_alerts[:5] # Tomar solo las 5 más recientes
    
    html_alerts = render_to_string('includes/live_alerts.html', {
        'mixed_alerts': all_alerts
    })
        
    data = {
        'total_trucks': Truck.objects.count(),
        'active_trucks': Truck.objects.filter(status='ACTIVE').count(),
        'recent_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').count(),
        'trucks_map': trucks_map_data,
        'latest_alerts_html': html_alerts
    }
    return JsonResponse(data)

def dashboard_view(request):
    """Renderiza el dashboard principal con KPIs reales de la BD."""
    # Autogenerar si está vacío
    if not Truck.objects.exists():
        call_command('mock_fleet', action='generate', count=20)
        
    # Mover camiones para que cada vez que entres se vea diferente
    simulate_live_tick()
    
    # Datos para el mapa interactivo (Camiones con coordenadas y alertas simuladas)
    trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    trucks_map_data = []
    
    import random
    alert_types = [
        "Pérdida Crítica de Presión (Llanta TR-2)",
        "Temperatura Alta (Eje Trasero)",
        "Alerta HOS: Límite de Ciclo",
        "Exceso de Peso Detectado",
        "Sensor de Llanta Desconectado"
    ]
    
    for t in trucks_qs:
        # Asignar alertas aleatorias si está en Mantenimiento o Inactivo
        active_alert = ""
        if t.status == 'MAINTENANCE':
            active_alert = random.choice([alert_types[1], alert_types[4]])
        elif t.status == 'INACTIVE':
            active_alert = random.choice([alert_types[0], alert_types[2], alert_types[3]])
            
        trucks_map_data.append({
            'plate': t.plate,
            'brand': t.brand,
            'status': t.status,
            'lat': float(t.latitude),
            'lon': float(t.longitude),
            'active_alert': active_alert
        })
    
    context = {
        'total_trucks': Truck.objects.count(),
        'active_trucks': Truck.objects.filter(status='ACTIVE').count(),
        'total_stations': TruckStop.objects.count() + AlternativeFuelStation.objects.count(),
        'recent_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').count(),
        'overweight_inspections': WeightInspection.objects.filter(is_overweight=True).count(),
        
        # Últimas alertas para el panel lateral
        'latest_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').order_by('-timestamp')[:2],
        'latest_weight_alerts': WeightInspection.objects.filter(is_overweight=True).order_by('-timestamp')[:2],
        
        # Mapa en JSON
        'trucks_map_json': trucks_map_data
    }
    
    # Pre-renderizar alertas iniciales
    latest_hos = HOSAlert.objects.filter(status='ACTIVE').order_by('-timestamp')[:4]
    latest_weight = WeightInspection.objects.filter(is_overweight=True).order_by('-timestamp')[:4]
    all_alerts = []
    for h in latest_hos:
        all_alerts.append({'type': 'hos', 'obj': h, 'ts': h.timestamp})
    for w in latest_weight:
        all_alerts.append({'type': 'weight', 'obj': w, 'ts': w.timestamp})
    all_alerts.sort(key=lambda x: x['ts'], reverse=True)
    context['mixed_alerts'] = all_alerts[:5]
    
    return render(request, "dashboard.html", context)

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