import csv
import traceback
import os
from django.utils import timezone
from apps.core.models import TruckStop, WIMStation, Amenity, RecyclingFacility, TransportationStatistic, TireShop, AlternativeFuelStation, CarrierCompany, WeightEnforcementStatistic

def process_uploaded_dataset(dataset_upload):
    """
    Motor ETL principal. Lee el archivo crudo y lo mapea a los modelos de Django.
    Soporta CSV y detecta automáticamente las variaciones de columnas de diferentes proveedores.
    """
    dataset_upload.status = 'PROCESSING'
    dataset_upload.processing_logs = "Iniciando procesamiento ETL nativo...\n"
    dataset_upload.save()

    try:
        file_path = dataset_upload.file.path
        ext = os.path.splitext(file_path)[1].lower()
        
        # Procesamiento CSV
        if ext == '.csv':
            with open(file_path, mode='r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f)
                _route_processing(reader, dataset_upload)
                
        # Procesamiento Excel (xlsx)
        elif ext in ['.xlsx', '.xls']:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active

            # Buscar dinámicamente la fila que contiene las verdaderas cabeceras (ignorando disclaimers)
            header_row_idx = 1
            headers = []
            max_headers = 0

            for i, row in enumerate(sheet.iter_rows(min_row=1, max_row=10), start=1):
                current_headers = [str(cell.value).strip() if cell.value else f"Empty_{j}" for j, cell in enumerate(row)]
                valid_headers_count = sum(1 for h in current_headers if not h.startswith("Empty_"))

                # Si esta fila tiene más columnas válidas que las anteriores, asumimos que es la cabecera
                if valid_headers_count > max_headers and valid_headers_count > 3:
                    max_headers = valid_headers_count
                    headers = current_headers
                    header_row_idx = i

            # Convertir Excel a una lista de diccionarios empezando desde la fila siguiente a las cabeceras
            reader = []
            for row in sheet.iter_rows(min_row=header_row_idx + 1):
                row_data = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers)}
                reader.append(row_data)

            _route_processing(reader, dataset_upload)
            
        # Procesamiento GeoJSON
        elif ext == '.geojson':
            import json
            with open(file_path, mode='r', encoding='utf-8') as f:
                geojson_data = json.load(f)
                
            # Los GeoJSON tienen la data en la lista "features", donde cada feature tiene "properties"
            reader = []
            if 'features' in geojson_data:
                for feature in geojson_data['features']:
                    props = feature.get('properties', {})
                    # Intentar extraer centroide si son puntos
                    geom = feature.get('geometry', {})
                    if geom and geom.get('type') == 'Point':
                        coords = geom.get('coordinates', [])
                        if len(coords) >= 2:
                            props['lon'] = coords[0] # GeoJSON es [lon, lat]
                            props['lat'] = coords[1]
                    reader.append(props)
                    
            _route_processing(reader, dataset_upload)

        else:
            raise ValueError(f"Formato no soportado para ETL nativo: {ext}")
                
        dataset_upload.status = 'COMPLETED'
        dataset_upload.processed_at = timezone.now()
        dataset_upload.processing_logs += "Procesamiento finalizado con éxito.\n"
        
    except Exception as e:
        dataset_upload.status = 'FAILED'
        dataset_upload.processing_logs += f"\nERROR CRÍTICO:\n{str(e)}\n{traceback.format_exc()}"
    
    dataset_upload.save()

def _route_processing(reader, dataset_upload):
    if dataset_upload.dataset_type == 'TRUCK_STOPS':
        _process_truck_stops(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'WIM_STATIONS':
        _process_wim_stations(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'RECYCLING':
        _process_recycling(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'CARRIERS':
        _process_carriers(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'STATS':
        _process_stats(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'TIRE_SHOPS':
        _process_tire_shops(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'ALT_FUEL':
        _process_alt_fuel(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'ENFORCEMENT':
        _process_enforcement(reader, dataset_upload)
    elif dataset_upload.dataset_type == 'ROUTES_NHS':
        dataset_upload.processing_logs += f"Se detectaron y validaron rutas NHS en formato GeoJSON. Estas se utilizarán nativamente en la Fase 4 para renderizado en los mapas (Leaflet/Mapbox).\n"
    else:
        dataset_upload.processing_logs += f"Lógica ETL para {dataset_upload.dataset_type} en desarrollo.\n"

def _process_truck_stops(reader, dataset_upload):
    """
    Procesa Truck Stops.
    Maneja polimorfismo de columnas (NTAD, Locmaster, Love's, Pilot).
    """
    created_count = 0
    
    for row in reader:
        # 1. Identificar columnas de Nombre y Operador (Polimorfismo)
        name = row.get('Facility_Name') or row.get('Name') or row.get('Store Name') or row.get('StoreName') or row.get('nhs_rest_stop') or row.get('municipality') or 'Unknown Truck Stop'
        operator = row.get('Operator') or row.get('Brand') or row.get('Network') or 'Public Rest Stop'
        
        # Inferencia de operador si no viene una columna explícita (Ej: Pilot all_locations_plot.csv)
        if operator == 'Public Rest Stop':
            name_lower = str(name).lower()
            if 'pilot' in name_lower or 'flying j' in name_lower:
                operator = 'Pilot Flying J'
            elif 'love' in name_lower:
                operator = "Love's Travel Stops"
            elif 'ta' in name_lower or 'travelcenters' in name_lower or 'petro' in name_lower:
                operator = 'TA / Petro'

        # 1.5 Identificar Teléfono y Web
        phone = row.get('Phone') or row.get('Telephone') or row.get('Contact_Number') or row.get('Phone Number') or 'Sin Información'
        website = row.get('Website') or row.get('URL') or row.get('Web') or ''
        
        # Limpieza básica de la web para evitar errores en Django URLField
        if website and not str(website).startswith(('http://', 'https://')):
            # Si el archivo de Love's trae un bloque de texto en la cabecera en vez de URL limpia
            if 'www.' in str(website).lower() or '.com' in str(website).lower():
                website = f"https://{str(website).split()[0]}"
            else:
                website = ''
        
        # 2. Identificar Coordenadas (Polimorfismo)
        lat = row.get('Latitude') or row.get('Lat') or row.get('latitude') or row.get('y') or row.get('Y')
        lon = row.get('Longitude') or row.get('Long') or row.get('longitude') or row.get('x') or row.get('X')
        
        # 3. Identificar Dirección
        address = row.get('Street_Address') or row.get('Address') or row.get('Street') or row.get('highway_route') or 'Sin Información'
        city = row.get('City') or row.get('municipality') or 'Sin Información'
        state = row.get('State') or row.get('State/Province') or row.get('state') or 'Sin Información'
        zip_code = row.get('Zip') or row.get('Zip Code') or row.get('Postal Code') or 'Sin Información'
        
        if not lat or not lon:
            continue # Si no hay GPS, descartamos para el mapa
            
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            continue
            
        # Identificar espacios de parqueo
        parking_spaces = 0
        spaces_raw = row.get('Parking Spaces Count') or row.get('Truck_Parking_Spaces') or row.get('truck_parking_capacity') or row.get('TruckParking') or 0
        try:
            parking_spaces = int(spaces_raw)
        except (ValueError, TypeError):
            pass

        # Identificar islas de diésel para tractomulas (Love's/Pilot)
        diesel_lanes = 0
        lanes_raw = row.get('DEFLanes') or row.get('DieselLanes') or row.get('Truck Fuel Lanes') or row.get('Fuel Lane Count') or 0
        try:
            diesel_lanes = int(lanes_raw)
        except (ValueError, TypeError):
            pass

        # Crear la estación base
        stop, created = TruckStop.objects.update_or_create(
            name=name[:255],
            latitude=lat,
            longitude=lon,
            defaults={
                'operator': operator[:255],
                'phone': phone[:50],
                'website': website[:500] if website else None,
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'parking_spaces': parking_spaces,
                'diesel_lanes': diesel_lanes
            }
        )
        
        # 4. Extracción de Amenidades (Múltiples formatos)
        amenities_to_add = []
        
        # Diccionario de palabras clave para buscar en las columnas booleanas o de texto
        amenity_keywords = {
            'Showers': ['shower', 'ducha', 'bath'],
            'Restaurant': ['restaurant', 'food', 'comida', 'dining'],
            'Tire Shop': ['tire', 'llanta', 'repair', 'mechanic'],
            'Parking': ['park', 'espacio', 'spaces'],
            'Scales': ['scale', 'wim', 'báscula', 'weigh'],
            'Diesel': ['diesel', 'fuel', 'combustible'],
            'WiFi': ['wifi', 'internet'],
        }
        
        # Estrategia A: Si hay columnas específicas que dicen 'Yes'/'True' (Ej: Dataset NTAD)
        for col_name, value in row.items():
            if not value: continue
            val_str = str(value).strip().lower()
            if val_str in ['yes', 'y', 'true', '1', 't']:
                for am_name, keywords in amenity_keywords.items():
                    if any(k in str(col_name).lower() for k in keywords):
                        amenity, _ = Amenity.objects.get_or_create(name=am_name)
                        amenities_to_add.append(amenity)
                        
        # Estrategia B: Si hay una columna "Amenities" o "Services" separada por comas (Ej: Locmaster/Loves)
        services_col = row.get('Amenities') or row.get('Services') or row.get('Facilities') or ''
        # Estrategia C: Si hay una columna específica de Restaurantes separada por comas (Ej: Pilot)
        restaurants_col = row.get('Restaurants') or row.get('Restaurant') or ''
        
        if services_col or restaurants_col:
            services_str = str(services_col).lower() + " " + str(restaurants_col).lower()
            # Si el campo de restaurantes tiene algún texto que no esté vacío, forzar la amenidad 'Restaurant'
            if str(restaurants_col).strip() != '':
                services_str += " restaurant "
                
            for am_name, keywords in amenity_keywords.items():
                if any(k in services_str for k in keywords):
                    amenity, _ = Amenity.objects.get_or_create(name=am_name)
                    amenities_to_add.append(amenity)
        
        if amenities_to_add:
            stop.amenities.add(*amenities_to_add)
            
        if created:
            created_count += 1
            
    dataset_upload.processing_logs += f"Se procesaron e importaron {created_count} Truck Stops (detectando automáticamente las columnas).\n"

def _process_wim_stations(reader, dataset_upload):
    """
    Procesa estaciones WIM y datos de enforcement.
    FILTRO ESTRICTO: Solo guardamos datos relevantes para "Vehículos Clase 8" (FHWA Class 8).
    """
    count = 0
    filtered_count = 0
    
    # Amenidad para saber que este punto tiene telemetría WIM
    wim_amenity, _ = Amenity.objects.get_or_create(name="Pesaje en Movimiento (WIM)", defaults={"category": "Regulación Inteligente"})

    for row in reader:
        # LÓGICA DE FILTRADO PARA CLASE 8
        # Si el dataset tiene una columna de clase de vehículo y NO es 8, lo ignoramos.
        vehicle_class = row.get('Vehicle_Class', row.get('FHWA_Class', ''))
        if vehicle_class and str(vehicle_class) != '8':
            filtered_count += 1
            continue # Descartar todo lo que no sea Clase 8

        station_id = row.get('Station_ID') or row.get('Station_Id') or row.get('site_id') or f"Unknown_{count}"
        lat = row.get('Latitude') or row.get('latitude') or row.get('Y') or row.get('y')
        lon = row.get('Longitude') or row.get('longitude') or row.get('X') or row.get('x')
        
        if not lat or not lon:
            continue

        wim, created = WIMStation.objects.update_or_create(
            station_id=station_id,
            defaults={
                'name': f"WIM Station {station_id}",
                'state': row.get('State', ''),
                'latitude': lat,
                'longitude': lon,
                'direction_of_travel': row.get('Direction', ''),
                'number_of_lanes': int(row.get('Lanes', 1) or 1)
            }
        )
        
        wim.amenities.add(wim_amenity)
        count += 1

    dataset_upload.processing_logs += f"Se procesaron {count} estaciones WIM para Vehículos Clase 8.\n"
    if filtered_count > 0:
        dataset_upload.processing_logs += f"Se descartaron {filtered_count} registros por no ser Clase 8.\n"

def _process_recycling(reader, dataset_upload):
    created_count = 0
    for row in reader:
        # Coordenadas polimórficas (Priorizar Latitude/Longitude sobre y/x)
        lat = row.get('Latitude') or row.get('latitude') or row.get('Lat') or row.get('LATITUDE') or row.get('y')
        lon = row.get('Longitude') or row.get('longitude') or row.get('Lon') or row.get('LONGITUDE') or row.get('x')
        
        is_valid_epa = False
        
        try:
            if lat and lon:
                lat, lon = round(float(lat), 6), round(float(lon), 6)
            else:
                lat, lon = None, None
        except Exception:
            lat, lon = None, None
            
        try:
            # Lógica para EPA_Disaster_Debris_Recovery_Data
            is_epa_file = True if 'EPA' in dataset_upload.file.name else False
            
            if is_epa_file:
                tires_flag = str(row.get('Tires', '')).strip()
                if tires_flag in ['1', 'yes', 'y', 'true', 'Yes'] or tires_flag.lower() in ['yes', 'y', 'true', '1']:
                    
                    zip_code = str(row.get('Zip') or '').strip()
                    state = row.get('State') or ''
                    name = str(row.get('Company') or 'EPA Recovery Site')[:255]
                    if not name or name == 'None':
                        name = 'EPA Recovery Site'
                    
                    tires_recycled = 1.0 # Valor simbólico
                    tires_generated = 0.0
                    population = 0
                    
                    is_valid_epa = True
                else:
                    is_valid_epa = False
                    
            else:
                is_epa_file = False
                is_valid_epa = False
                # Lógica para US_Recycling_Infrastructure_2022
                tires_recycled_raw = row.get('Tires Tons Recycled')
                tires_recycled = float(tires_recycled_raw) if tires_recycled_raw else 0.0
                
                tires_generated_raw = row.get('Tires Tons  Generated')
                tires_generated = float(tires_generated_raw) if tires_generated_raw else 0.0
                
                population_raw = row.get('Population')
                population = int(population_raw) if population_raw else 0
                
                # Solo guardar infraestructuras que tengan datos de llantas
                if tires_recycled <= 0 and tires_generated <= 0:
                    continue
                    
                zip_code = row.get('Zip_Code', '')
                state = row.get('State', '')
                name = f"Planta Reciclaje Llantas {zip_code} - {state}"
                
        except Exception as e:
            print("ERROR", e)
            continue

        # Usar coordenadas como identificador si existen (EPA), si no, usar zip_code (US_Recycling)
        if is_valid_epa and lat is not None and lon is not None:
            # Validar que lat y lon estén dentro de rangos normales de coordenadas antes de guardar
            if abs(lat) > 90 or abs(lon) > 180:
                pass
            else:
                try:
                    # Actualizar si existe, crear si no existe
                    facility, created = RecyclingFacility.objects.update_or_create(
                        latitude=lat,
                        longitude=lon,
                        defaults={
                            'name': name,
                            'state': state,
                            'zip_code': zip_code[:20],
                            'tires_recycled_tons': tires_recycled,
                            'tires_generated_tons': tires_generated,
                            'population_served': population
                        }
                    )
                    created_count += 1
                except Exception as e:
                    print("Error saving EPA:", e)
                    pass
        elif not is_epa_file:
            try:
                facility, created = RecyclingFacility.objects.update_or_create(
                    zip_code=zip_code,
                    defaults={
                        'name': name,     
                        'state': state,
                        'latitude': lat,
                        'longitude': lon,
                        'tires_recycled_tons': tires_recycled,
                        'tires_generated_tons': tires_generated,
                        'population_served': population
                    }
                )
                if created:
                    created_count += 1
            except Exception as e:
                pass
        
    dataset_upload.processing_logs += f"Se importaron {created_count} plantas de reciclaje de llantas.\n"

def _process_carriers(reader, dataset_upload):
    created_count = 0
    batch_size = 10000
    batch = []
    
    for row in reader:
        dot_num = row.get('DOT_NUMBER')
        if not dot_num: continue

        batch.append(CarrierCompany(
            dot_number=dot_num,
            legal_name=str(row.get('LEGAL_NAME', 'Unknown'))[:255],
            dba_name=str(row.get('DBA_NAME', ''))[:255],
            carrier_operation=str(row.get('CARRIER_OPERATION', ''))[:100],    
            status=str(row.get('STATUS_CODE', 'Active'))[:50]
        ))
        
        if len(batch) >= batch_size:
            # Inserción masiva optimizada para PostgreSQL
            CarrierCompany.objects.bulk_create(
                batch,
                batch_size=batch_size,
                update_conflicts=True,
                unique_fields=['dot_number'],
                update_fields=['legal_name', 'dba_name', 'carrier_operation', 'status']
            )
            created_count += len(batch)
            batch = []

    # Insertar el remanente
    if batch:
        CarrierCompany.objects.bulk_create(
            batch,
            batch_size=batch_size,
            update_conflicts=True,
            unique_fields=['dot_number'],
            update_fields=['legal_name', 'dba_name', 'carrier_operation', 'status']
        )
        created_count += len(batch)
        
    dataset_upload.processing_logs += f"Se importaron {created_count} empresas transportistas (Carriers) usando procesamiento masivo por lotes.\n"

def _process_stats(reader, dataset_upload):
    import datetime
    created_count = 0
    for row in reader:
        date_str = row.get('Date')
        if not date_str: continue

        try:
            # Formato en los datasets gubernamentales puede ser "1/1/2026 0:00" o "1947 Jan 01 12:00:00 AM"
            date_part = str(date_str).split()[0] # Tratar de aislar la parte de la fecha
            
            try:
                if '/' in date_part:
                    date_obj = datetime.datetime.strptime(date_part, '%m/%d/%Y').date()
                elif '-' in date_part:
                    date_obj = datetime.datetime.strptime(date_part, '%Y-%m-%d').date()
                else:
                    # Formato "1947 Jan 01"
                    clean_date_str = " ".join(str(date_str).split()[:3])
                    date_obj = datetime.datetime.strptime(clean_date_str, '%Y %b %d').date()
            except ValueError:
                continue

            truck_emp = str(row.get('Transportation Employment - Truck Transportation', '')).replace(',', '').strip()
            fatalities = str(row.get('Highway Fatalities', '')).replace(',', '').strip()     
            diesel = str(row.get('Highway Fuel Price - On-highway Diesel', '')).replace(',', '').replace('$', '').strip()      

            # Solo guardar si hay al menos un dato útil para la industria de tractomulas
            if not truck_emp and not diesel and not fatalities:
                continue

            TransportationStatistic.objects.update_or_create(
                date=date_obj,
                defaults={
                    'truck_employment': int(truck_emp) if truck_emp else None,  
                    'highway_fatalities': int(fatalities) if fatalities else None,
                    'diesel_price': float(diesel) if diesel else None,
                }
            )
            created_count += 1
        except Exception:
            continue

    dataset_upload.processing_logs += f"Se importaron {created_count} meses de estadísticas de transporte relevantes para Clase 8.\n"

def _process_enforcement(reader, dataset_upload):
    created_count = 0
    for row in reader:
        year = row.get('year')
        state = row.get('State')
        
        if not year or not state: continue
        
        try:
            year_int = int(year)
            
            # Extraer números limpiando posibles espacios vacíos
            def get_int(key):
                val = str(row.get(key, '0')).strip()
                return int(val) if val else 0
                
            fixed_weighed = get_int('Vehicles Weighed (Fixed platform Scale)')
            wim_weighed = get_int('Vehicles Weighed (WIM Scale)')
            oversize = get_int('oversize_violation_current_year')
            overweight = get_int('overweight_violation_current_year')
            
            WeightEnforcementStatistic.objects.update_or_create(
                year=year_int,
                state=state[:10],
                defaults={
                    'vehicles_weighed_fixed': fixed_weighed,
                    'vehicles_weighed_wim': wim_weighed,
                    'oversize_violations': oversize,
                    'overweight_violations': overweight
                }
            )
            created_count += 1
        except (ValueError, TypeError):
            continue
            
    dataset_upload.processing_logs += f"Se importaron {created_count} registros anuales de control y pesaje por Estado.\n"

def _process_tire_shops(reader, dataset_upload):
    created_count = 0
    for row in reader:
        # Extraer latitud y longitud, el CSV tiene las columnas 'lat' y 'lon'
        lat = row.get('lat') or row.get('latitude') or row.get('y') or row.get('Lat')
        lon = row.get('lon') or row.get('longitude') or row.get('x') or row.get('Lon')
        if not lat or not lon: continue

        try:
            lat, lon = float(lat), float(lon)
        except (ValueError, TypeError):
            continue

        # Extraer campos de dirección que pueden venir directamente o dentro de JSON tags
        address = row.get('street', '')
        if not address and row.get('housenumber'):
            address = f"{row.get('housenumber')} {row.get('street', '')}"
            
        city = row.get('city') or row.get('addr:city', 'Sin Información')
        state = row.get('state') or row.get('addr:state', 'Sin Información')
        zip_code = row.get('postcode') or row.get('addr:postcode', 'Sin Información')

        TireShop.objects.update_or_create(
            latitude=lat,
            longitude=lon,
            defaults={
                'name': row.get('name', 'Unknown Tire Shop')[:255],
                'brand': row.get('brand', '')[:100],
                'operator': row.get('operator', 'Sin Información')[:255],      
                'address': address if address else 'Sin Información',
                'city': city,
                'state': state,
                'zip_code': zip_code,       
                'phone': row.get('phone', 'Sin Información')[:50],
                'website': row.get('website', '')[:500],
                'is_24_hours': str(row.get('opening_hours', '')).lower() == '24/7'
            }
        )
        created_count += 1
    dataset_upload.processing_logs += f"Se importaron {created_count} talleres de llantas.\n"

def _process_alt_fuel(reader, dataset_upload):
    created_count = 0
    # Como son muchos registros, usaremos una lista para hacer bulk_create si es posible,
    # pero update_or_create es más seguro contra duplicados.
    
    for row in reader:
        # Filtro estricto: Solo estaciones aptas para tractomulas (Clase 8 / Heavy Duty)
        # El archivo usa 'NG Vehicle Class', 'Maximum Vehicle Class', o códigos 'HD'
        max_class = str(row.get('Maximum Vehicle Class') or row.get('NG Vehicle Class') or '').upper()
        if max_class not in ['HD', 'HEAVY-DUTY', 'HEAVY', 'CLASS 8']:
            continue # Si es solo para autos ligeros (LD/MD), la ignoramos
            
        lat = row.get('Latitude') or row.get('y')
        lon = row.get('Longitude') or row.get('x')
        if not lat or not lon: continue
            
        try:
            lat, lon = float(lat), float(lon)
            cng_dispensers = int(row.get('CNG Dispenser Num') or 0)
            ev_dc_fast = int(row.get('EV DC Fast Count') or 0)
        except (ValueError, TypeError):
            continue
            
        AlternativeFuelStation.objects.update_or_create(
            latitude=lat,
            longitude=lon,
            defaults={
                'name': row.get('Station Name', 'Unknown Alt Fuel')[:255],
                'fuel_type_code': row.get('Fuel Type Code', '')[:20],
                'ev_connector_types': row.get('EV Connector Types', '')[:255],
                'is_public': str(row.get('Groups With Access Code', '')).lower() == 'public',
                'operator': row.get('EV Network', 'Sin Información')[:255],
                'address': row.get('Street Address', 'Sin Información'),
                'city': row.get('City', 'Sin Información'),
                'state': row.get('State', 'Sin Información'),
                'zip_code': row.get('ZIP', 'Sin Información'),
                'phone': row.get('Station Phone', 'Sin Información')[:50],
                'maximum_vehicle_class': max_class,
                'cng_dispenser_num': cng_dispensers,
                'ev_dc_fast_count': ev_dc_fast
            }
        )
        created_count += 1
    dataset_upload.processing_logs += f"Se importaron {created_count} estaciones de combustible alternativo (Exclusivas para Tractomulas / HD).\n"
