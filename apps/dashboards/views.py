from django.views.generic import TemplateView
from apps.devices.models import Truck
from apps.fleet.models import Trip
from apps.hos_monitoring.models import HOSAlert, Driver
from apps.weight_monitoring.models import WeightInspection
import json

class DashboardsHubView(TemplateView):
    template_name = 'dashboards/hub.html'

class ResumenView(TemplateView):
    template_name = 'dashboards/resumen.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.core.views import simulate_live_tick
        
        # Mover camiones para el efecto en vivo
        simulate_live_tick()
        
        # KPIs
        context['total_trucks'] = Truck.objects.count()
        context['active_trucks'] = Truck.objects.filter(status='ACTIVE').count()
        context['maintenance_trucks'] = Truck.objects.filter(status='MAINTENANCE').count()
        context['inactive_trucks'] = context['total_trucks'] - context['active_trucks'] - context['maintenance_trucks']
        
        context['active_trips'] = Trip.objects.filter(status='IN_TRANSIT').count()
        context['completed_trips'] = Trip.objects.filter(status='COMPLETED').count()
        
        # Sincronización lógica de alertas HOS
        context['hos_alerts'] = HOSAlert.objects.filter(status='ACTIVE').count()
        context['weight_alerts'] = WeightInspection.objects.filter(is_overweight=True).count()
        
        # Datos para gráficas (JSON)
        fleet_status = {
            'labels': ['Activos', 'En Mantenimiento', 'Inactivos'],
            'values': [context['active_trucks'], context['maintenance_trucks'], context['inactive_trucks']]
        }
        context['fleet_status_json'] = fleet_status
        
        # Datos para el mapa (Todos los camiones con coordenadas)
        trucks_qs = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
        trucks_map_data = []
        for t in trucks_qs:
            trucks_map_data.append({
                'id': t.id,
                'plate': t.plate,
                'brand': t.brand,
                'status': t.status,
                'lat': float(t.latitude),
                'lon': float(t.longitude)
            })
        context['trucks_map_json'] = trucks_map_data
        
        return context

class MonitoreoIoTView(TemplateView):
    template_name = 'dashboards/monitoreo_iot.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        from datetime import timedelta
        import random
        
        trucks_count = Truck.objects.count()
        if trucks_count == 0:
            trucks_count = 12 # Fallback si no hay generadas
            
        # KPIs de Magnitud
        context['active_sensors'] = trucks_count * 19 # 1 Gateway + 18 Sensores por tractomula
        context['data_processed_24h'] = context['active_sensors'] * 2880 # Asumiendo 1 ping cada 30 seg
        context['system_latency'] = random.randint(12, 28) # ms
        context['network_health'] = 99.8 # %
        
        # Datos Simulados para Gráficas Plotly (Últimas 2 horas, intervalos de 5 min)
        times = [(timezone.now() - timedelta(minutes=i*5)).strftime('%H:%M') for i in range(24)][::-1]
        
        # Generar una curva de temperatura que sube y se estabiliza
        base_temp = 100.0
        temp_data = []
        for i in range(24):
            base_temp += random.uniform(-0.5, 2.0)
            if base_temp > 130: base_temp -= 2.0
            temp_data.append(round(base_temp, 1))
            
        # Generar curva de presión estable con pequeñas fluctuaciones
        pressure_data = [round(random.uniform(98.5, 102.5), 1) for _ in range(24)]
        
        context['iot_timeseries_json'] = {
            'times': times,
            'pressure': pressure_data,
            'temp': temp_data
        }
        
        # --- NUEVO: Lista de vehículos para la vista de flota ---
        # Simulamos que tenemos miles, pero mostramos los que requieren atención prioritaria
        trucks = Truck.objects.all()[:50] # Limitamos para no saturar la vista inicial
        fleet_list = []
        
        for i, t in enumerate(trucks):
            # Simular estado
            status_sim = 'OK'
            if i % 7 == 0: status_sim = 'WARNING'
            if i % 12 == 0: status_sim = 'CRITICAL'
            
            # Último ping hiper-realista (5 a 15 segundos para la mayoría)
            # Solo los que están en modo crítico o warning grave podrían tener latencias mayores si perdieron señal
            if status_sim == 'CRITICAL' and i % 3 == 0:
                ping_str = f"Hace {random.randint(1, 3)} min"
            else:
                ping_str = f"Hace {random.randint(2, 12)} seg"
            
            fleet_list.append({
                'id': t.id,
                'plate': t.plate,
                'brand': t.brand,
                'model': t.model,
                'status': status_sim,
                'last_ping': ping_str,
                'avg_temp': round(random.uniform(100, 110), 1) if status_sim == 'OK' else round(random.uniform(120, 150), 1),
                'avg_psi': round(random.uniform(95, 105), 1) if status_sim == 'OK' else round(random.uniform(70, 90), 1),
                'avg_wear': round(random.uniform(12.0, 18.0), 1) if status_sim == 'OK' else round(random.uniform(1.5, 4.5), 1)
            })
            
        context['fleet_list'] = fleet_list
        context['fleet_list_json'] = fleet_list
        
        return context

class AlertasView(TemplateView):
    template_name = 'dashboards/alertas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mocks para Centro de Alertas y Mantenimiento
        alertas = [
            {'id': 'ALT-001', 'truck': 'T-1001', 'brand': 'Freightliner', 'type': 'Pérdida de Presión', 'sensor': 'TR-2', 'severity': 'CRITICAL', 'time': 'Hace 5 min'},
            {'id': 'ALT-002', 'truck': 'T-2005', 'brand': 'Kenworth', 'type': 'Temperatura Alta', 'sensor': 'RL-3', 'severity': 'WARNING', 'time': 'Hace 45 min'},
            {'id': 'ALT-003', 'truck': 'SIM-105', 'brand': 'Kenworth', 'type': 'Batería Baja', 'sensor': 'HUB-1', 'severity': 'WARNING', 'time': 'Hace 2 horas'},
            {'id': 'ALT-004', 'truck': 'SIM-108', 'brand': 'Peterbilt', 'type': 'Sensor Desconectado', 'sensor': 'FR-1', 'severity': 'CRITICAL', 'time': 'Hace 12 min'}
        ]
        
        mantenimientos = [
            {'id': 'WO-992', 'truck': 'T-3001', 'type': 'Reemplazo Llanta TR-4', 'status': 'IN_PROGRESS', 'eta': '2 Horas'},
            {'id': 'WO-993', 'truck': 'SIM-101', 'type': 'Alineación y Balanceo', 'status': 'PENDING', 'eta': 'Mañana 08:00 AM'},
            {'id': 'WO-990', 'truck': 'T-1005', 'type': 'Parcheo Rápido RL-1', 'status': 'COMPLETED', 'eta': 'Finalizado'}
        ]
        
        context['alertas'] = alertas
        context['mantenimientos'] = mantenimientos
        context['criticas_count'] = sum(1 for a in alertas if a['severity'] == 'CRITICAL')
        context['warning_count'] = sum(1 for a in alertas if a['severity'] == 'WARNING')
        context['mantenimiento_count'] = len([m for m in mantenimientos if m['status'] in ['IN_PROGRESS', 'PENDING']])
        
        return context

class HOSComplianceView(TemplateView):
    template_name = 'dashboards/hos_compliance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Real HOS Data from the database (Generated by mock_fleet command)
        total_drivers = Driver.objects.filter(status='ACTIVE').count()
        if total_drivers == 0:
            total_drivers = 15 # mock fallback
            
        active_violations = HOSAlert.objects.filter(is_resolved=False).count()
        
        # Generar KPIs para la vista
        context['kpis'] = {
            'active_drivers': total_drivers,
            'hos_violations': active_violations,
            'avg_drive_time': '7h 45m', # Hardcoded trend
            'compliance_score': f"{max(0, 100 - (active_violations * 2))}%"
        }
        
        # 2. Gráfico de Dona: Distribución de Estados Duty (ELD)
        context['duty_labels'] = ['Driving', 'On-Duty', 'Sleeper Berth', 'Off-Duty']
        context['duty_values'] = [45, 20, 25, 10]
        
        # 3. Gráfico de Barras: Riesgo de Fatiga por Hora del Día
        context['timeline_hours'] = ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00']
        context['timeline_risk'] = [5, 12, 25, 45, 80, 95, 60]
        
        # 4. Tabla de Conductores en Riesgo
        context['risk_drivers'] = [
            {'name': 'Carlos Mendoza', 'truck': 'SIM-101', 'rule': 'Límite 11h (Conducción)', 'time_left': '0h 15m', 'status': 'Crítico', 'action': 'Obligar Parada'},
            {'name': 'John Smith', 'truck': 'T-2005', 'rule': 'Límite 14h (On-Duty)', 'time_left': '0h 45m', 'status': 'Alerta', 'action': 'Buscar Truck Stop'},
            {'name': 'Miguel Santos', 'truck': 'SIM-105', 'rule': 'Descanso 30 min', 'time_left': '1h 10m', 'status': 'Alerta', 'action': 'Notificar'},
            {'name': 'Sarah Connor', 'truck': 'SIM-112', 'rule': 'Ciclo 70h/8 Días', 'time_left': '12h 00m', 'status': 'Óptimo', 'action': 'Ninguna'},
        ]
        
        # Agregar alertas reales si existen
        real_alerts = HOSAlert.objects.filter(is_resolved=False).order_by('-created_at')[:3]
        if real_alerts.exists():
            context['risk_drivers'] = []
            for alert in real_alerts:
                context['risk_drivers'].append({
                    'name': alert.driver.user.get_full_name() if alert.driver else 'Desconocido',
                    'truck': 'N/A', # Si estuviera mapeado
                    'rule': alert.get_violation_type_display(),
                    'time_left': 'Infracción',
                    'status': 'Crítico',
                    'action': 'Contactar Inmediato'
                })
        
        return context

class DesgasteLlantasView(TemplateView):
    template_name = 'dashboards/desgaste_llantas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        from datetime import timedelta
        import random
        
        # Mocks para Desgaste de Llantas
        context['total_tires_monitored'] = 306 # 17 tractomulas * 18 llantas
        context['critical_wear'] = random.randint(3, 8)
        context['warning_wear'] = random.randint(15, 25)
        context['good_wear'] = context['total_tires_monitored'] - context['critical_wear'] - context['warning_wear']
        
        # Distribución de desgaste para Plotly (Pie Chart)
        context['wear_distribution_json'] = {
            'labels': ['Óptimo (>10/32")', 'Advertencia (5/32"-10/32")', 'Crítico (<5/32")'],
            'values': [context['good_wear'], context['warning_wear'], context['critical_wear']]
        }
        
        # Tendencia de vida útil proyectada
        months = [(timezone.now() + timedelta(days=30*i)).strftime('%b %Y') for i in range(6)]
        replacements = [random.randint(5, 20) for _ in range(6)]
        
        context['replacement_forecast_json'] = {
            'months': months,
            'replacements': replacements
        }
        
        # Vehículos con mayor desgaste (Top 5)
        top_wear_trucks = []
        trucks = Truck.objects.filter(status='ACTIVE')[:5]
        for t in trucks:
            top_wear_trucks.append({
                'plate': t.plate,
                'worst_tire': f"{random.choice(['FL', 'FR', 'RL', 'RR'])}-{random.randint(1,4)}",
                'tread_depth': round(random.uniform(2.0, 4.5), 1),
                'est_miles_left': random.randint(500, 3000)
            })
        context['top_wear_trucks'] = top_wear_trucks
        
        return context

class PesoVehiculoView(TemplateView):
    template_name = 'dashboards/peso_vehiculo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        from datetime import timedelta
        import random
        
        # Mocks para Regulación y Peso
        trucks = Truck.objects.filter(status='ACTIVE')
        total_trucks = trucks.count()
        if total_trucks == 0: total_trucks = 17
        
        # KPIs
        context['weigh_ins_24h'] = random.randint(45, 120)
        context['overweight_violations'] = WeightInspection.objects.filter(is_overweight=True).count()
        context['avg_gross_weight'] = round(random.uniform(72000, 78000), 0)
        context['wim_bypasses'] = random.randint(15, 40) # Bypass pre-clearance
        
        # Tendencia de Violaciones de Peso (Últimos 7 días)
        days = [(timezone.now() - timedelta(days=i)).strftime('%b %d') for i in range(7)][::-1]
        violations_trend = [random.randint(0, 5) for _ in range(7)]
        violations_trend[-1] = context['overweight_violations'] # Sync with DB
        
        context['weight_trend_json'] = {
            'days': days,
            'violations': violations_trend
        }
        
        # Distribución de Carga por Eje (Promedio de la flota)
        context['axle_distribution_json'] = {
            'labels': ['Steer (Dirección)', 'Drive (Tracción)', 'Trailer (Remolque)'],
            'values': [12000, 32000, 31500] # Typical loaded distribution in lbs
        }
        
        # Lista de vehículos cerca del límite (Live)
        heavy_trucks = []
        for i, t in enumerate(trucks[:8]):
            gross = round(random.uniform(75000, 82000), 0)
            is_violating = gross > 80000
            heavy_trucks.append({
                'plate': t.plate,
                'location': f"I-{random.choice(['10', '40', '80', '95', '35'])} Mile Marker {random.randint(10, 300)}",
                'gross_weight': gross,
                'status': 'VIOLATION' if is_violating else 'WARNING' if gross > 78000 else 'OK'
            })
        
        context['heavy_trucks'] = sorted(heavy_trucks, key=lambda x: x['gross_weight'], reverse=True)
        
        return context

class RecomendacionesView(TemplateView):
    template_name = 'dashboards/recomendaciones.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        import random
        from apps.devices.models import Truck
        
        trucks = Truck.objects.filter(status__in=['ACTIVE', 'WARNING', 'CRITICAL'])
        if not trucks.exists():
            trucks = Truck.objects.all()[:15]
            
        fleet_data = {}
        
        # 1. Datos Globales
        global_recs = [
            {
                'title': 'Desvío Sugerido por Tráfico',
                'desc': 'Se detectó tráfico pesado en I-35N. Sugerimos ruta alternativa por TX-130 para 3 tractomulas.',
                'impact': 'Ahorro est. 45 min c/u',
                'priority': 'HIGH', 'icon': 'fa-route', 'color': '#3b82f6',
                'badge_color': 'rgba(239, 68, 68, 0.2)', 'badge_text': '#ef4444', 'badge_label': 'Prioridad Alta'
            },
            {
                'title': 'Rotación Preventiva General',
                'desc': 'Las llantas de tracción de 5 vehículos presentan un desgaste irregular del 15% comparado con el eje trasero.',
                'impact': '+12% vida útil',
                'priority': 'MEDIUM', 'icon': 'fa-wrench', 'color': '#f59e0b',
                'badge_color': 'rgba(245, 158, 11, 0.2)', 'badge_text': '#f59e0b', 'badge_label': 'Media'
            },
            {
                'title': 'Ajuste de Presión en Frío',
                'desc': '12 unidades en la base norte reportan 3 PSI por debajo del ideal debido a la ola de frío nocturna.',
                'impact': 'Ahorro 2% combustible',
                'priority': 'LOW', 'icon': 'fa-temperature-arrow-down', 'color': '#10b981',
                'badge_color': 'rgba(16, 185, 129, 0.2)', 'badge_text': '#10b981', 'badge_label': 'Baja'
            }
        ]
        
        fleet_data['GLOBAL'] = {
            'plate': 'GLOBAL',
            'dropdown_label': '🌍 Flota Global',
            'kpis': {
                'efficiency': random.randint(88, 96),
                'fuel': round(random.uniform(150.0, 350.0), 1),
                'incidents': random.randint(5, 15),
                'optimizations': random.randint(10, 25)
            },
            'radar': [95, 88, 75, 92, 98, 85],
            'recs': global_recs
        }

        # 2. Datos por Vehículo
        for t in trucks:
            # Simular un estado lógico
            status_roll = random.random()
            if status_roll < 0.15:
                status = 'CRITICAL'
                status_icon = '🔴'
            elif status_roll < 0.40:
                status = 'WARNING'
                status_icon = '🟠'
            else:
                status = 'OK'
                status_icon = '🟢'

            t_radar = [random.randint(75, 100) for _ in range(6)]
            t_recs = []
            
            if status == 'CRITICAL':
                t_recs.append({'title': 'Detención Inmediata Sugerida', 'desc': f'La unidad {t.plate} presenta parámetros críticos en llantas. Detener en el próximo arcén seguro.', 'impact': 'Prevención de accidente', 'priority': 'HIGH', 'icon': 'fa-ban', 'color': '#ef4444'})
                t_radar[0] = random.randint(30, 50) # Seguridad baja
                t_radar[3] = random.randint(20, 40) # Mantenimiento crítico
            elif status == 'WARNING':
                t_recs.append({'title': 'Mantenimiento Preventivo', 'desc': f'Se detectó desgaste irregular o pérdida de presión anómala en {t.plate}. Programar revisión.', 'impact': 'Extiende vida útil 15%', 'priority': 'MEDIUM', 'icon': 'fa-wrench', 'color': '#f59e0b'})
                t_radar[3] = random.randint(50, 70) # Mantenimiento bajo
            else:
                t_recs.append({'title': 'Ruta Óptima', 'desc': f'La unidad {t.plate} está operando en parámetros ideales de eficiencia y seguridad. Mantener velocidad crucero.', 'impact': 'Ahorro de combustible', 'priority': 'LOW', 'icon': 'fa-check-circle', 'color': '#10b981'})
                
            if random.random() < 0.4:
                t_recs.append({'title': 'Ajuste de Velocidad', 'desc': 'Reducir velocidad a 60 mph por ráfagas de viento detectadas en la ruta actual.', 'impact': 'Ahorro 3% combustible', 'priority': 'LOW', 'icon': 'fa-wind', 'color': '#3b82f6'})

            # Formatear recs
            formatted_recs = []
            for r in t_recs:
                b_bg, b_txt, b_lbl = 'rgba(16, 185, 129, 0.2)', '#10b981', 'Baja'
                if r['priority'] == 'HIGH':
                    b_bg, b_txt, b_lbl = 'rgba(239, 68, 68, 0.2)', '#ef4444', 'Prioridad Alta'
                elif r['priority'] == 'MEDIUM':
                    b_bg, b_txt, b_lbl = 'rgba(245, 158, 11, 0.2)', '#f59e0b', 'Media'
                
                r['badge_color'] = b_bg
                r['badge_text'] = b_txt
                r['badge_label'] = b_lbl
                formatted_recs.append(r)

            fleet_data[t.plate] = {
                'plate': t.plate,
                'dropdown_label': f"{status_icon} {t.plate} - {t.brand}",
                'kpis': {
                    'efficiency': sum(t_radar) // 6,
                    'fuel': round(random.uniform(5.0, 20.0), 1),
                    'incidents': random.randint(0, 2),
                    'optimizations': len(formatted_recs)
                },
                'radar': t_radar,
                'recs': formatted_recs
            }

        context['fleet_data_json'] = fleet_data
        context['trucks_list'] = [{'plate': k, 'label': v['dropdown_label']} for k, v in fleet_data.items() if k != 'GLOBAL']
        
        return context

class GeoespacialView(TemplateView):
    template_name = 'dashboards/geoespacial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.devices.models import Truck
        from apps.core.views import simulate_live_tick
        import random
        
        # Avanzar la simulación para tener datos vivos
        simulate_live_tick()

        # KPIs Geoespaciales
        context['active_geofences'] = random.randint(8, 15)
        context['weather_alerts'] = random.randint(1, 3)
        context['route_deviations'] = random.randint(0, 2)
        context['restricted_zones'] = random.randint(3, 7)

        # Extraer camiones con coordenadas
        trucks = Truck.objects.filter(latitude__isnull=False, longitude__isnull=False)
        trucks_map_data = []
        for t in trucks:
            # Velocidad y rumbo simulado
            speed = random.randint(45, 75) if t.status == 'ACTIVE' else (random.randint(5, 20) if t.status == 'WARNING' else 0)
            heading = random.randint(0, 360)
            
            trucks_map_data.append({
                'id': t.id,
                'plate': t.plate,
                'brand': t.brand,
                'status': t.status,
                'lat': float(t.latitude),
                'lon': float(t.longitude),
                'speed': speed,
                'heading': heading
            })

        context['trucks_map_json'] = trucks_map_data
        
        # Zonas geocercadas simuladas (basadas en coordenadas centrales aprox. de EEUU)
        geofences = [
            {'name': 'Hub Dallas', 'lat': 32.7767, 'lon': -96.7970, 'radius': 50000, 'color': '#3b82f6'},
            {'name': 'Zona Clima Severo', 'lat': 39.7392, 'lon': -104.9903, 'radius': 150000, 'color': '#ef4444'},
            {'name': 'Restricción Urbana (OOS)', 'lat': 41.8781, 'lon': -87.6298, 'radius': 30000, 'color': '#f59e0b'}
        ]
        context['geofences_json'] = geofences

        # Mapa de Calor: Densidad de Servicios (Truck Stops, Parking, Amenities)
        heatmap_points = []
        base_centers = [
            (32.7767, -96.7970),  # Dallas
            (41.8781, -87.6298),  # Chicago
            (34.0522, -118.2437), # LA
            (39.7392, -104.9903), # Denver
            (33.7490, -84.3880),  # Atlanta
            (29.7604, -95.3698),  # Houston
            (40.7128, -74.0060),  # NY / NJ
        ]
        for lat, lon in base_centers:
            # Zonas de alta densidad (Ciudades principales y cruces de autopistas)
            for _ in range(150): # Aumentado masivamente
                heatmap_points.append([lat + random.uniform(-2.0, 2.0), lon + random.uniform(-2.0, 2.0), random.uniform(0.8, 1.0)])
            # Zonas de densidad media
            for _ in range(200):
                heatmap_points.append([lat + random.uniform(-5, 5), lon + random.uniform(-5, 5), random.uniform(0.4, 0.7)])
            # Zonas escasas (Gran cobertura nacional)
            for _ in range(100):
                heatmap_points.append([lat + random.uniform(-10, 10), lon + random.uniform(-10, 10), random.uniform(0.1, 0.3)])
                
        context['heatmap_json'] = heatmap_points

        return context

from apps.stations.models import TruckStation, TruckStopParking
import random

class EstacionesDescansoView(TemplateView):
    template_name = 'dashboards/estaciones_descanso.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Simulación de datos para el dashboard si no hay estaciones reales aún
        stations_count = TruckStation.objects.count()
        if stations_count == 0:
            total_stations = 1245
            total_parking_spots = 85400
            available_spots = int(total_parking_spots * random.uniform(0.15, 0.35)) # 15-35% disponible
        else:
            total_stations = stations_count
            total_parking_spots = sum([s.parking_spaces for s in TruckStation.objects.all()])
            available_spots = int(total_parking_spots * random.uniform(0.15, 0.35))
            
        context['total_stations'] = f"{total_stations:,}"
        context['total_parking_spots'] = f"{total_parking_spots:,}"
        context['available_spots'] = f"{available_spots:,}"
        context['occupancy_rate'] = round(((total_parking_spots - available_spots) / total_parking_spots) * 100, 1) if total_parking_spots else 0

        # Datos simulados para gráficas
        context['amenities_labels'] = ['Duchas', 'Restaurante', 'Mecánico', 'Diesel', 'WiFi']
        context['amenities_values'] = [85, 92, 45, 100, 70] # Porcentajes de cobertura
        
        # Red de descanso simulada para el mapa y la tabla
        context['top_stations'] = [
            {'name': 'Love\'s Travel Stop', 'location': 'I-35, Dallas, TX', 'spots': 120, 'available': 12, 'showers': True, 'mechanic': True, 'lat': 32.7767, 'lon': -96.7970},
            {'name': 'Pilot Travel Center', 'location': 'I-80, Chicago, IL', 'spots': 85, 'available': 3, 'showers': True, 'mechanic': False, 'lat': 41.8781, 'lon': -87.6298},
            {'name': 'TA Travel Center', 'location': 'I-10, Houston, TX', 'spots': 150, 'available': 45, 'showers': True, 'mechanic': True, 'lat': 29.7604, 'lon': -95.3698},
            {'name': 'Flying J Dealer', 'location': 'I-5, Los Angeles, CA', 'spots': 60, 'available': 0, 'showers': False, 'mechanic': True, 'lat': 34.0522, 'lon': -118.2437},
            {'name': 'Petro Stopping Center', 'location': 'I-75, Atlanta, GA', 'spots': 200, 'available': 80, 'showers': True, 'mechanic': True, 'lat': 33.7490, 'lon': -84.3880},
        ]
        
        return context

class CombustibleReciclajeView(TemplateView):
    template_name = 'dashboards/combustible_reciclaje.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- Simulando datos de Sostenibilidad y Economía Circular (EPA) ---
        
        # 1. KPIs Globales
        context['kpis'] = {
            'co2_saved': '1,245',        # Toneladas de CO2 mitigadas
            'tires_recycled': '342',     # Llantas enviadas a renovado/reciclaje
            'fuel_efficiency': '6.8',    # MPG Promedio de la flota
            'green_score': '92'          # Calificación de sostenibilidad (0-100)
        }

        # 2. Datos para el Gráfico de Barras: Destino Final de las Llantas (Economía Circular)
        context['tires_destiny_labels'] = ['Renovado (Retread)', 'Reciclaje (Asfalto/Caucho)', 'Desecho (Vertedero)']
        context['tires_destiny_values'] = [65, 30, 5]  # Porcentajes (Éxito del 95% en economía circular)

        # 3. Datos para el Gráfico de Líneas: Consumo de Combustible vs. Presión de Llantas (Impacto directo de PIN)
        # Demuestra cómo mantener el PSI correcto baja el consumo de Galones por Milla.
        context['fuel_trend_months'] = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        context['fuel_consumption'] = [18500, 18200, 17900, 17100, 16800, 16200] # Tendencia a la baja en galones
        
        # 4. Tabla de Auditoría EPA (Vehículos de alto impacto)
        context['epa_audit'] = [
            {'unit': 'SIM-101', 'mpg': '5.2', 'status': 'Crítico', 'co2': '+15%', 'action': 'Revisión Inyección/Llantas'},
            {'unit': 'SIM-105', 'mpg': '5.8', 'status': 'Alerta', 'co2': '+5%', 'action': 'Ajuste de Presión'},
            {'unit': 'SIM-112', 'mpg': '7.1', 'status': 'Óptimo', 'co2': '-10%', 'action': 'Ninguna'},
            {'unit': 'T-2005', 'mpg': '7.4', 'status': 'Óptimo', 'co2': '-12%', 'action': 'Ninguna'},
        ]

        return context

class RegulacionSeguridadView(TemplateView):
    template_name = 'dashboards/regulacion_seguridad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import random
        
        # Mocks para Auditorías DOT y Puntuación CSA
        context['kpis'] = {
            'csa_score': random.randint(35, 65), # Lower is better in CSA, but let's just show a number
            'dot_inspections': random.randint(15, 45),
            'oos_rate': f"{random.uniform(2.5, 5.5):.1f}%", # Out of Service rate
            'safety_warnings': random.randint(2, 8)
        }
        
        # Gráfico de Radar: CSA BASICs (Behavior Analysis and Safety Improvement Categories)
        context['csa_labels'] = ['Unsafe Driving', 'Crash Indicator', 'HOS Compliance', 'Vehicle Maint.', 'Ctrl. Substances', 'Driver Fitness']
        context['csa_values'] = [random.randint(10, 40), random.randint(5, 20), random.randint(15, 35), random.randint(25, 60), random.randint(0, 5), random.randint(5, 15)]
        
        # Gráfico de Barras: Historial de Inspecciones DOT por Nivel
        context['dot_levels'] = ['Level I (Full)', 'Level II (Walk-Around)', 'Level III (Driver/Cred)']
        context['dot_counts'] = [random.randint(5, 15), random.randint(10, 25), random.randint(15, 30)]
        
        # Tabla de Infracciones Recientes (OOS - Out of Service)
        context['recent_violations'] = [
            {'date': '2026-06-20', 'unit': 'T-1005', 'type': 'Frenos Desajustados', 'severity': 'OOS (Out of Service)', 'status': 'Resuelto'},
            {'date': '2026-06-18', 'unit': 'SIM-108', 'type': 'Luces Traseras Inoperantes', 'severity': 'Advertencia', 'status': 'Reparado'},
            {'date': '2026-06-15', 'unit': 'T-2001', 'type': 'Profundidad de Llanta < 2/32"', 'severity': 'OOS (Out of Service)', 'status': 'En Taller'},
            {'date': '2026-06-12', 'unit': 'SIM-115', 'type': 'Fuga de Aire del Sistema', 'severity': 'Crítico', 'status': 'Resuelto'},
        ]
        
        return context

class ModelosPredictivosView(TemplateView):
    template_name = 'dashboards/modelos_predictivos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import random
        from django.utils import timezone
        from datetime import timedelta
        
        # Mocks para Modelos Predictivos e IA
        context['kpis'] = {
            'model_accuracy': '94.2%',
            'predicted_failures': random.randint(3, 12),
            'prevented_downtime': f"{random.randint(120, 350)} hrs",
            'roi_estimation': f"${random.randint(15, 45)},000"
        }
        
        # Gráfico de Líneas: Riesgo de Falla vs Tiempo (Días)
        days = [(timezone.now() + timedelta(days=i)).strftime('%b %d') for i in range(10)]
        context['forecast_days'] = days
        context['risk_fleet_a'] = [random.randint(10, 20) + (i * 2) for i in range(10)] # Tendencia al alza
        context['risk_fleet_b'] = [random.randint(30, 40) - (i * 1.5) for i in range(10)] # Tendencia a la baja (mantenimiento)
        
        # Gráfico de Dispersión (Scatter): Clustering de Vida Útil de Llantas
        # Eje X: Millas Recorridas, Eje Y: Profundidad de Banda (32nds)
        scatter_data = []
        for _ in range(50):
            miles = random.randint(10000, 150000)
            # Relación inversa: más millas, menos profundidad, con algo de ruido
            base_depth = 20 - (miles / 10000)
            depth = max(2, base_depth + random.uniform(-3, 3))
            scatter_data.append({'x': miles, 'y': round(depth, 1)})
            
        context['tire_scatter_json'] = scatter_data
        
        # Tabla de Predicciones de Falla a Corto Plazo
        context['upcoming_failures'] = [
            {'unit': 'SIM-105', 'component': 'Llanta Drive (Tracción)', 'probability': '89%', 'eta': '3-5 Días', 'impact': 'Alto (Posible Blowout)'},
            {'unit': 'T-2001', 'component': 'Sistema de Frenos (Fuga)', 'probability': '75%', 'eta': '1 Semana', 'impact': 'Medio (OOS DOT)'},
            {'unit': 'SIM-112', 'component': 'Llanta Steer (Direccional)', 'probability': '92%', 'eta': '24-48 Horas', 'impact': 'Crítico (Seguridad)'},
            {'unit': 'T-1008', 'component': 'Batería Sensor TPMS', 'probability': '99%', 'eta': '12 Horas', 'impact': 'Bajo (Pérdida de Señal)'},
        ]
        
        return context
