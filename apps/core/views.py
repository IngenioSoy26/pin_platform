from pathlib import Path
import json
import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from apps.core.models import (
    AlternativeFuelStation,
    RecyclingFacility,
    TireShop,
    TruckStop,
    WIMStation,
)
from apps.data_ingestion.models import DataSource
from apps.devices.models import Truck
from apps.hos_monitoring.models import HOSAlert
from apps.weight_monitoring.models import WeightInspection

_DEMO_ROUTES_CACHE = {
    "mtime": None,
    "routes": None,
}


def _iter_geojson_features(file_path, max_features=None):
    decoder = json.JSONDecoder()
    buffer = ""
    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                return
            buffer += chunk
            idx = buffer.find('"features"')
            if idx != -1:
                buffer = buffer[idx:]
                break

        start = buffer.find("[")
        while start == -1:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                return
            buffer += chunk
            start = buffer.find("[")

        buffer = buffer[start + 1 :]
        yielded = 0

        while True:
            buffer = buffer.lstrip(" \t\r\n,")
            if buffer.startswith("]"):
                return

            try:
                feature, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    return
                buffer += chunk
                continue

            buffer = buffer[end:]
            yielded += 1
            yield feature
            if max_features and yielded >= max_features:
                return


def _extract_latlon_points(geometry):
    if not geometry:
        return []

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")

    if geom_type == "LineString" and isinstance(coords, list):
        sequences = [coords]
    elif geom_type == "MultiLineString" and isinstance(coords, list):
        sequences = coords
    else:
        return []

    points = []
    last = None
    for seq in sequences:
        if not isinstance(seq, list):
            continue
        for item in seq:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            lon, lat = item[0], item[1]
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                continue

            current = (lat, lon)
            if last is not None and current == last:
                continue
            last = current
            points.append([lat, lon])

    return points


def _downsample_points(points, max_points=500):
    if len(points) <= max_points:
        return points
    step = max(1, int(len(points) / max_points))
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


def _load_demo_routes(limit=10):
    dataset = DataSource.objects.filter(file_type="GEOJSON").order_by("-last_load").first()
    if not dataset or not dataset.file_path or not Path(dataset.file_path).exists():
        return []

    mtime = Path(dataset.file_path).stat().st_mtime
    if _DEMO_ROUTES_CACHE["routes"] is not None and _DEMO_ROUTES_CACHE["mtime"] == mtime:
        return _DEMO_ROUTES_CACHE["routes"]

    excluded_stfips = {2, 15, 72}
    routes_by_id = {}
    ordered_ids = []

    for feature in _iter_geojson_features(dataset.file_path, max_features=20000):
        props = feature.get("properties") or {}
        stfips = props.get("STFIPS")
        try:
            stfips_int = int(stfips)
        except (TypeError, ValueError):
            continue
        if stfips_int in excluded_stfips:
            continue

        routeid = props.get("ROUTEID") or props.get("RouteId") or props.get("routeid")
        if not routeid:
            continue
        raw_name = props.get("LNAME") or props.get("Lname") or props.get("lname") or ""
        raw_name = str(raw_name).strip()
        if not raw_name:
            sign1 = str(props.get("SIGN1") or "").strip()
            signn1 = str(props.get("SIGNN1") or "").strip()
            if sign1 and signn1:
                raw_name = f"{sign1} {signn1}"
            elif sign1:
                raw_name = sign1
            else:
                raw_name = str(routeid)
        lname = raw_name
        key = f"{stfips_int}-{routeid}"

        points = _extract_latlon_points(feature.get("geometry") or {})
        if not points:
            continue

        sample_lat, sample_lon = points[len(points) // 2]
        if not (24.0 <= sample_lat <= 50.0 and -125.0 <= sample_lon <= -66.0):
            continue

        if key not in routes_by_id:
            routes_by_id[key] = {"id": key, "name": str(lname), "coords": []}
            ordered_ids.append(key)

        routes_by_id[key]["coords"].extend(points)
        if len(routes_by_id[key]["coords"]) > 4000:
            routes_by_id[key]["coords"] = _downsample_points(routes_by_id[key]["coords"], max_points=2000)

        ready = [
            rid
            for rid in ordered_ids[:limit]
            if len(routes_by_id[rid]["coords"]) >= 200
        ]
        if len(ready) >= limit:
            break

    routes = []
    for rid in ordered_ids:
        route = routes_by_id[rid]
        if len(route["coords"]) < 80:
            continue
        route["coords"] = _downsample_points(route["coords"], max_points=500)
        routes.append(route)
        if len(routes) >= limit:
            break

    _DEMO_ROUTES_CACHE["mtime"] = mtime
    _DEMO_ROUTES_CACHE["routes"] = routes
    return routes


def _lerp(a, b, t):
    return a + (b - a) * t


def _demo_fleet_snapshot():
    routes = _load_demo_routes(limit=10)
    if not routes:
        return []

    now = time.time()
    trucks = []
    total = 28

    for idx in range(total):
        route = routes[idx % len(routes)]
        coords = route["coords"]
        if len(coords) < 2:
            continue

        offset = (idx + 1) * 37.0
        speed_points_per_sec = 0.35
        position = (now * speed_points_per_sec + offset) % (len(coords) - 1)
        i = int(position)
        frac = position - i
        lat = _lerp(coords[i][0], coords[i + 1][0], frac)
        lon = _lerp(coords[i][1], coords[i + 1][1], frac)

        if idx < 22:
            status = "ACTIVE"
        elif idx < 26:
            status = "MAINTENANCE"
        else:
            status = "INACTIVE"

        trucks.append(
            {
                "plate": f"DEMO-{idx + 1:03d}",
                "brand": "Tractomula Demo",
                "status": status,
                "lat": lat,
                "lon": lon,
                "active_alert": "",
                "route_id": route["id"],
                "route_name": route["name"],
                "route_pos": position,
                "is_demo": True,
            }
        )

    return trucks

def api_live_dashboard(request):
    """Endpoint AJAX para refrescar los datos del dashboard en tiempo real."""
    demo_mode = request.GET.get("demo") == "1"
    trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    trucks_map_data = []
    if demo_mode or not trucks_qs.exists():
        trucks_map_data = _demo_fleet_snapshot()
        total_trucks = len(trucks_map_data)
        active_trucks = sum(1 for t in trucks_map_data if t["status"] == "ACTIVE")
    else:
        for t in trucks_qs:
            trucks_map_data.append(
                {
                    "plate": t.plate,
                    "brand": t.brand,
                    "status": t.status,
                    "lat": float(t.latitude),
                    "lon": float(t.longitude),
                    "active_alert": "",
                }
            )
        total_trucks = Truck.objects.count()
        active_trucks = Truck.objects.filter(status="ACTIVE").count()

    from django.template.loader import render_to_string

    latest_hos = HOSAlert.objects.filter(status='ACTIVE').order_by('-timestamp')[:4]
    latest_weight = WeightInspection.objects.filter(is_overweight=True).order_by('-timestamp')[:4]

    all_alerts = []
    for h in latest_hos:
        all_alerts.append({'type': 'hos', 'obj': h, 'ts': h.timestamp})
    for w in latest_weight:
        all_alerts.append({'type': 'weight', 'obj': w, 'ts': w.timestamp})

    all_alerts.sort(key=lambda x: x['ts'], reverse=True)
    all_alerts = all_alerts[:5]

    html_alerts = render_to_string('includes/live_alerts.html', {
        'mixed_alerts': all_alerts
    })

    data = {
        'total_trucks': total_trucks,
        'active_trucks': active_trucks,
        'recent_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').count(),
        'trucks_map': trucks_map_data,
        'latest_alerts_html': html_alerts,
        'is_demo': demo_mode or not trucks_qs.exists(),
    }
    return JsonResponse(data)

def dashboard_view(request):
    """Renderiza el dashboard principal con KPIs reales de la BD."""
    demo_mode = request.GET.get("demo") == "1"
    trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
    trucks_map_data = []
    if demo_mode or not trucks_qs.exists():
        trucks_map_data = _demo_fleet_snapshot()
        total_trucks = len(trucks_map_data)
        active_trucks = sum(1 for t in trucks_map_data if t["status"] == "ACTIVE")
    else:
        for t in trucks_qs:
            trucks_map_data.append(
                {
                    "plate": t.plate,
                    "brand": t.brand,
                    "status": t.status,
                    "lat": float(t.latitude),
                    "lon": float(t.longitude),
                    "active_alert": "",
                }
            )
        total_trucks = Truck.objects.count()
        active_trucks = Truck.objects.filter(status="ACTIVE").count()

    context = {
        'total_trucks': total_trucks,
        'active_trucks': active_trucks,
        'total_stations': TruckStop.objects.count() + AlternativeFuelStation.objects.count(),
        'recent_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').count(),
        'overweight_inspections': WeightInspection.objects.filter(is_overweight=True).count(),

        'latest_hos_alerts': HOSAlert.objects.filter(status='ACTIVE').order_by('-timestamp')[:2],
        'latest_weight_alerts': WeightInspection.objects.filter(is_overweight=True).order_by('-timestamp')[:2],

        'trucks_map_json': trucks_map_data,
        'fleet_is_demo': demo_mode or not trucks_qs.exists(),
    }

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
    preferred_files = [
        settings.MEDIA_ROOT / "datasets" / "routes_colored_simplified.geojson",
        settings.MEDIA_ROOT / "datasets" / "routes_simplified.geojson",
        settings.MEDIA_ROOT / "datasets" / "routes_interstate_simplified.geojson",
    ]

    for route_file in preferred_files:
        if route_file.exists():
            return JsonResponse({"url": f"{settings.MEDIA_URL}datasets/{route_file.name}"})

    dataset = DataSource.objects.filter(file_type='GEOJSON').order_by('-last_load').first()
    if dataset and dataset.file_path:
        dataset_path = Path(dataset.file_path)
        if dataset_path.exists():
            try:
                relative_path = dataset_path.relative_to(settings.MEDIA_ROOT)
                return JsonResponse({"url": f"{settings.MEDIA_URL}{relative_path.as_posix()}"})
            except ValueError:
                pass

    return JsonResponse({'url': None}, status=404)


def api_demo_routes(request):
    return JsonResponse({"routes": _load_demo_routes(limit=10)})

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
