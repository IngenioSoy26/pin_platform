📄 DOCUMENTO MAESTRO: "PIN Platform - Guía de Construcción Completa"

**Copia TODO este contenido y pégalo en un archivo Word. Este es tu "manual de construcción" que le pasarás a la IA.**





---

```markdown
# 🚛 PIN PLATFORM - DOCUMENTO MAESTRO DE CONSTRUCCIÓN
## Proyecto de Maestría Big Data - UNIR + Ambientronika
### Alumno: Gustavo Alonzo Segrera Gomez
### Fecha límite: 25/06/2026

---

## 📋 INSTRUCCIONES PARA LA IA QUE GENERARÁ EL CÓDIGO

**CONTEXTO:** Eres un Arquitecto de Software Senior experto en IoT, Django, PostgreSQL/PostGIS, Machine Learning y normativas de transporte de EE.UU. (FMCSA, DOT).

**OBJETIVO:** Generar el código COMPLETO y FUNCIONAL de "PIN Platform", una plataforma web IoT + Big Data para monitoreo de llantas en tractomulas.

**REGLAS OBLIGATORIAS:**
1. Genera el código archivo por archivo, indicando la ruta exacta
2. TODO el código debe ser funcional y ejecutable
3. NO omitas archivos ni dejes placeholders como "# TODO" o "pass"
4. Si un archivo es muy largo, divídelo en partes numeradas
5. Usa type hints y docstrings en TODO el código
6. Sigue PEP 8 estrictamente
7. Al final de cada fase, indica cómo probar lo generado

**RUTA BASE DEL PROYECTO:**
C:\Users\gusta\Desktop\Maestria\0.1. Practicas\DB_TRUNCK\PAQUETE_COMPARTIBLE_DB_TRUNCK\pin_platform\

---

## 🎯 CONTEXTO DEL NEGOCIO (LEER CON ATENCIÓN)

**PIN** es un sistema IoT para tractomulas en EE.UU. con:

### Arquitectura de Hardware:
- **1 DISPOSITIVO MAESTRO** por tractomula (en cabina): GPS, SIM 4G/5G, CPU, batería, acelerómetro, OBD-II
- **18 SENSORES ESCLAVOS** (uno por llanta): presión, temperatura, vibración
- Comunicación: Bluetooth Mesh entre sensores y maestro, 4G/5G del maestro a la nube

### Posiciones de las 18 llantas:
- FL-1, FL-2 (Front Left Outer/Inner) - STEER
- FR-1, FR-2 (Front Right Outer/Inner) - STEER
- RL-1 a RL-4 (Rear Left) - DRIVE
- RR-1 a RR-4 (Rear Right) - DRIVE
- TL-1 a TL-4 (Trailer Left) - TRAILER
- TR-1 a TR-4 (Trailer Right) - TRAILER

### Funciones del Sistema:
1. Monitorear en tiempo real 18 llantas por tractomula
2. Detectar anomalías: desgastes, pinchazos, baja presión, sobrecalentamiento
3. Monitorear cumplimiento HOS (Hours of Service - FMCSA)
4. Monitorear peso del vehículo (Federal Bridge Formula)
5. Predecir desgaste de llantas con 20+ parámetros
6. Recomendar al conductor: tiendas de llantas, descanso, comida, reciclaje
7. Generar dashboards interactivos y reportes predictivos

---

## 📚 REGULACIONES DE EE.UU. QUE EL SISTEMA DEBE CUMPLIR

### 1. HOURS OF SERVICE (HOS) - FMCSA 49 CFR Part 395
- 11-Hour Driving Limit: Máximo 11h conducción tras 10h off-duty
- 14-Hour Limit: No conducir después de 14h on-duty
- 30-Minute Break: Descanso 30 min tras 8h acumuladas conducción
- 60/70-Hour Limit: 60h en 7 días o 70h en 8 días
- 10-Hour Off-Duty: Mínimo 10h descanso antes de reiniciar ciclo
- Sleeper Berth: Puede dividir 10h en 7h + 2h
- Adverse Conditions: +2h en condiciones adversas
- Short-Haul Exception: Exento si radio 150 air-miles + 14h máximo

### 2. PROFUNDIDAD MÍNIMA DE BANDA - FMCSA 49 CFR 393.75
- Steer (FL, FR): Mínimo legal 4/32", recomendado PIN 6/32"
- Drive (RL, RR): Mínimo legal 2/32", recomendado PIN 4/32"
- Trailer (TL, TR): Mínimo legal 2/32", recomendado PIN 4/32"

### 3. FEDERAL BRIDGE GROSS WEIGHT FORMULA - 23 CFR 658.17
- Peso total vehículo: 80,000 lbs máximo federal
- Eje simple: 20,000 lbs
- Tándem de ejes: 34,000 lbs
- Fórmula: W = 500[L/(N-1) + 6N + 36]

---

## 🧮 FÓRMULA DE PREDICCIÓN DE DESGASTE (IMPLEMENTAR)

```
desgaste_32nds = (millas/1000) * tasa_base * 
                 factor_presion * factor_temperatura * factor_velocidad * 
                 factor_carga * factor_vibracion * factor_conduccion * 
                 factor_ambiente * factor_ruta * factor_mantenimiento
```

### Factores de ajuste:
- factor_presion = 1 + 0.02 * |PSI_actual - PSI_recomendado| / PSI_recomendado
- factor_temperatura = 1 + 0.005 * max(0, temp_f - 120)
- factor_velocidad = 1 + 0.01 * max(0, speed_mph - 55)
- factor_carga = (carga_actual / carga_nominal)^1.25
- factor_vibracion = 1 + 2 * max(0, vibration_g - 0.5)
- factor_conduccion = 1 + 0.02 * hard_events_per_100mi
- factor_ambiente = 1.0 + ajustes por clima
- factor_ruta = 1.0 + ajustes por tipo de vía
- factor_mantenimiento = 1.0 + ajustes por rotación/align/balance

---

## 🗂️ PLAN DE CONSTRUCCIÓN POR FASES (10 FASES)

### ⚠️ IMPORTANTE: EJECUTAR EN ESTE ORDEN EXACTO

---

### 🔷 FASE 1: ESTRUCTURA BASE Y CONFIGURACIÓN (30 min)

**Objetivo:** Crear la estructura del proyecto Django con todas las carpetas y archivos de configuración.

**Archivos a generar:**
1. `manage.py`
2. `requirements.txt` (con todas las dependencias)
3. `.env` (variables de entorno)
4. `.gitignore`
5. `README.md` (instrucciones completas)
6. `config/__init__.py`
7. `config/settings/__init__.py`
8. `config/settings/base.py` (configuración principal con PostGIS)
9. `config/settings/dev.py`
10. `config/settings/prod.py`
11. `config/urls.py` (URLs principales)
12. `config/wsgi.py`
13. `config/asgi.py`
14. `config/celery.py`

**Crear todas las carpetas de apps (con __init__.py):**
- apps/core/
- apps/data_ingestion/
- apps/devices/
- apps/iot_ingestion/
- apps/tires/
- apps/hos_monitoring/
- apps/weight_monitoring/
- apps/alerts/
- apps/recommendations/
- apps/stations/
- apps/routes/
- apps/fuel_alternative/
- apps/recycling/
- apps/regulation/
- apps/carriers/
- apps/analytics/
- apps/dashboards/
- apps/api/

**También crear:**
- templates/ (con includes/)
- static/css/, static/js/, static/img/
- ml_models/
- scripts/
- docs/

**Al terminar:** Verificar que `python manage.py check` no dé errores.

---

### 🔷 FASE 2: APP CORE - MODELOS BASE (20 min)

**Objetivo:** Crear los modelos abstractos base y utilidades compartidas.

**Archivos a generar:**
1. `apps/core/__init__.py`
2. `apps/core/apps.py`
3. `apps/core/models.py` con:
   - `BaseModel` (abstracto: created_at, updated_at, is_active)
   - `GeoBaseModel` (abstracto: location PointField, address, city, state, zip_code, country)
4. `apps/core/admin.py`
5. `apps/core/utils.py` con:
   - `create_point_from_coords(lat, lng)`
   - `get_nearby(model_class, point, radius_km)`
   - `calculate_distance(point1, point2)`
6. `apps/core/management/__init__.py`
7. `apps/core/management/commands/__init__.py`
8. `apps/core/management/commands/inspect_existing_db.py`

**Al terminar:** Verificar que los modelos abstractos no generen migraciones.

---

### 🔷 FASE 3: APP DEVICES - GESTIÓN DE DISPOSITIVOS (30 min)

**Objetivo:** Modelar la jerarquía Truck → MasterDevice → TireSensor.

**Archivos a generar:**
1. `apps/devices/__init__.py`
2. `apps/devices/apps.py`
3. `apps/devices/models.py` con:
   - `Truck` (vin, plate, brand, model, year, num_tires, carrier FK, status, location)
   - `MasterDevice` (device_code, truck OneToOne, firmware, sim_card, battery, signal, status)
   - `TireSensor` (sensor_code, master_device FK, position 18 opciones, tire_brand, install_date, lifecycle_km, accumulated_km)
   - `VehicleReading` (master_device FK, timestamp, GPS, speed, heading, OBD-II, accelerometer, battery)
4. `apps/devices/admin.py` (con GISModelAdmin)
5. `apps/devices/serializers.py` (GeoJSON)
6. `apps/devices/views.py` (ViewSet con acciones: list, stats, map_data)
7. `apps/devices/urls.py`
8. `apps/devices/services.py`

**Al terminar:** Ejecutar `python manage.py makemigrations devices`

---

### 🔷 FASE 4: APP TIRES - MONITOREO Y DESGASTE (45 min)

**Objetivo:** Modelar lecturas de sensores, configuración de posiciones y desgaste.

**Archivos a generar:**
1. `apps/tires/__init__.py`
2. `apps/tires/apps.py`
3. `apps/tires/models.py` con:
   - `TirePositionConfig` (position 18 opciones, axle_type, new/warning/critical tread depth, pressure, temp, load, lifecycle, wear_rate)
   - `TireReading` (sensor FK, timestamp, pressure_psi, temperature_f, vibration_g, estimated_tread_depth, rssi, battery)
   - `TireMaintenanceLog` (sensor FK, maintenance_type, timestamp, mileage, tread_before/after, notes, cost)
4. `apps/tires/admin.py`
5. `apps/tires/serializers.py`
6. `apps/tires/views.py` (con acciones: readings, wear_prediction, maintenance_history)
7. `apps/tires/urls.py`
8. `apps/tires/services.py` con:
   - `TireWearCalculator` que implemente TODA la fórmula de desgaste con los 10 factores
   - `predict_remaining_life(sensor)`
   - `get_wear_factors(sensor)`
9. `apps/tires/wear_formulas.py` con todas las funciones de factores

**Al terminar:** Verificar que la fórmula de desgaste esté completamente implementada.

---

### 🔷 FASE 5: APP HOS_MONITORING - HORAS DE SERVICIO (40 min)

**Objetivo:** Implementar monitoreo completo de Hours of Service FMCSA.

**Archivos a generar:**
1. `apps/hos_monitoring/__init__.py`
2. `apps/hos_monitoring/apps.py`
3. `apps/hos_monitoring/models.py` con:
   - `Driver` (first_name, last_name, license_number, license_state, cdl_class, hire_date, status)
   - `DriverLog` (driver FK, truck FK, timestamp, status DRIVING/ON_DUTY/OFF_DUTY/SLEEPER, location, odometer)
   - `HOSCompliance` (driver OneToOne, cycle_start, cycle_type, driving_time_today, on_duty_time_today, consecutive_driving_time, hours_7days, hours_8days, last_10h_off, last_30min_break, is_short_haul, adverse_conditions, is_compliant)
   - `HOSAlert` (driver FK, alert_type 11 opciones, severity, title, message, timestamp, location, current_value, threshold_value, status)
4. `apps/hos_monitoring/admin.py`
5. `apps/hos_monitoring/serializers.py`
6. `apps/hos_monitoring/views.py`
7. `apps/hos_monitoring/urls.py`
8. `apps/hos_monitoring/services.py` con:
   - `HOSCalculator` que implemente TODAS las reglas FMCSA
   - `check_compliance(driver)` que valide las 8 reglas
   - `update_hos_status(driver)` que actualice tiempos acumulados
   - `generate_hos_alerts(driver)` que genere alertas según umbrales
9. `apps/hos_monitoring/fmcsa_rules.py` con todas las constantes y reglas

**Al terminar:** Verificar que las 8 reglas HOS estén implementadas.

---

### 🔷 FASE 6: APP WEIGHT_MONITORING - CONTROL DE PESO (30 min)

**Objetivo:** Implementar monitoreo de peso según Federal Bridge Formula.

**Archivos a generar:**
1. `apps/weight_monitoring/__init__.py`
2. `apps/weight_monitoring/apps.py`
3. `apps/weight_monitoring/models.py` con:
   - `WeightRegulation` (state, state_name, federal/state limits, permits, weight_wear_factor)
   - `AxleConfiguration` (truck FK, axle_number, axle_type, position_ft, tire_count, max_weight, current_weight)
   - `WeightInspection` (truck FK, timestamp, location, inspection_type, gross_weight, axle_weights, is_overweight, state)
4. `apps/weight_monitoring/admin.py`
5. `apps/weight_monitoring/serializers.py`
6. `apps/weight_monitoring/views.py`
7. `apps/weight_monitoring/urls.py`
8. `apps/weight_monitoring/services.py` con:
   - `BridgeFormulaCalculator` que implemente W = 500[L/(N-1) + 6N + 36]
   - `check_weight_compliance(truck)` que valide límites
   - `calculate_weight_distribution(truck)`
   - `get_overweight_alerts(truck)`
9. `apps/weight_monitoring/bridge_formula.py`

**Al terminar:** Verificar que la fórmula del puente esté correctamente implementada.

---

### 🔷 FASE 7: APPS RESTANTES (stations, routes, fuel, recycling, regulation, carriers) (60 min)

**Objetivo:** Crear las apps que consumen los 16 datasets estáticos.

**Para CADA app generar:**
- `__init__.py`, `apps.py`, `models.py`, `admin.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`

**Apps específicas:**

#### 7.1 stations (Estaciones PILOT/LOVES/TravelCenters)
- Modelo: `TruckStation` (name, operator, brand, phone, website, has_diesel/def/restaurant/wifi/showers/tires/mechanic, parking_spaces, location)
- Modelo: `TruckStopParking`
- Acciones: nearby, stats

#### 7.2 routes (Rutas NHS)
- Modelo: `HighwayRoute` (route_id, route_name, route_type, state, length_km, route_geometry LineString)
- Acciones: stats, by_state

#### 7.3 fuel_alternative (Combustible alternativo)
- Modelo: `AlternativeFuelStation` (name, fuel_type CNG/LNG/ELEC/H2, is_hd_fuel, access_type, operators)
- Acciones: hd_stations, stats

#### 7.4 recycling (Centros de reciclaje EPA)
- Modelo: `RecyclingCenter` (name, capacity_tons, recycling_type, accepts_tires)
- Acciones: tire_recycling, stats

#### 7.5 regulation (WIM y regulaciones)
- Modelo: `WIMStation` (name, station_code, direction, location)
- Modelo: `SizeWeightRegulation` (state, max_weight_lbs, max_length_ft, max_width_in, max_height_ft)
- Acciones: stats

#### 7.6 carriers (Transportistas FMCSA + BTS)
- Modelo: `Carrier` (dot_number, legal_name, dba_name, entity_type, num_power_units, num_drivers, state)
- Modelo: `MonthlyTransportIndicator` (date, indicator_name, value, unit, region)
- Acciones: top_fleets, trends

**Al terminar:** Verificar que todas las apps tengan modelos y puedan hacer migrate.

---

### 🔷 FASE 8: APPS CRÍTICAS - ALERTS, RECOMMENDATIONS, IOT_INGESTION (60 min)

**Objetivo:** Implementar el corazón del negocio PIN.

#### 8.1 alerts (Sistema de alertas integral)
**Modelo Alert con 15+ tipos:**
- Llantas: LOW_PRESSURE, HIGH_PRESSURE, HIGH_TEMPERATURE, PUNCTURE, TIRE_WEAR_WARNING, TIRE_WEAR_CRITICAL, SENSOR_OFFLINE, LOW_BATTERY_SENSOR, LOW_BATTERY_MASTER
- Conducción: HARD_BRAKING, HARD_ACCELERATION
- HOS: todas las de HOSAlert
- Peso: OVERWEIGHT_AXLE, OVERWEIGHT_GROSS

**Modelo Alert con:**
- truck FK, sensor FK (nullable), alert_type, severity (INFO/LOW/MEDIUM/HIGH/CRITICAL)
- title, message, trigger_value, threshold_value, unit
- location, timestamp, status (ACTIVE/ACKNOWLEDGED/RESOLVED)
- acknowledged_at, resolved_at, resolution_notes

**Servicios:**
- `AlertEngine` que reciba lecturas IoT y genere alertas automáticamente
- `check_tire_alerts(reading)` - valida presión, temp, vibración
- `check_hos_alerts(driver)` - valida reglas HOS
- `check_weight_alerts(truck)` - valida peso

#### 8.2 recommendations (Motor de recomendaciones)
**Modelo Recommendation con 9 tipos:**
- TIRE_SHOP, REST_STOP, RESTAURANT, FUEL_STATION, ALT_FUEL, RECYCLING_CENTER, WIM_STATION, HOTEL, MECHANIC

**Modelo con:**
- alert FK (nullable), truck FK, rec_type, priority (1-10)
- target_name, target_address, target_location PointField
- distance_km, estimated_time_min, estimated_cost_usd
- reason, status (GENERATED/SENT/ACCEPTED/REJECTED/COMPLETED)

**Servicios (5 motores):**
- `TireShopRecommender` - busca tiendas especializadas en radio 50km
- `RestStopRecommender` - sugiere parada tras 8h conducción
- `RestaurantRecommender` - recomienda en horas de comida
- `RecyclingRecommender` - sugiere centro EPA si llanta debe reciclarse
- `FuelRecommender` - sugiere combustible alternativo

#### 8.3 iot_ingestion (API de ingesta de datos IoT)
**Endpoint crítico:**
```
POST /api/iot/reading/
{
  "device_code": "PIN-MASTER-001",
  "timestamp": "2026-06-18T14:30:00Z",
  "vehicle_data": {
    "latitude": 41.8781,
    "longitude": -87.6298,
    "speed_mph": 65,
    "heading": 180,
    "rpm": 1800,
    "odometer": 250000,
    "accel_x": 0.02,
    "accel_y": -0.01,
    "accel_z": 0.98,
    "battery_level": 85,
    "signal_strength": -65
  },
  "tire_readings": [
    {"position": "FL-1", "pressure_psi": 98, "temperature_f": 118, "vibration_g": 0.22},
    ... (18 lecturas)
  ]
}
```

**Procesamiento:**
1. Validar datos (rangos aceptables)
2. Guardar VehicleReading
3. Guardar 18 TireReading
4. Actualizar HOSCompliance del conductor
5. Ejecutar AlertEngine
6. Si hay alertas, ejecutar RecommendationEngine
7. Responder con ack + alertas generadas + recomendaciones

**Al terminar:** Verificar que el endpoint POST funcione con curl.

---

### 🔷 FASE 9: ANALYTICS - 6 MODELOS ML (60 min)

**Objetivo:** Implementar los 6 modelos de Machine Learning.

**Modelo 1: TireWearPredictor (XGBoost + fórmula física híbrida)**
- Input: 20+ parámetros (presión, temp, carga, velocidad, vibración, conducción, clima, ruta, mantenimiento)
- Output: wear_percent, miles_remaining, days_remaining
- Métricas: R² > 0.85, MAE < 5%

**Modelo 2: TireFailurePredictor (LSTM TensorFlow)**
- Input: Series temporales 24h (presión, temp, vibración)
- Output: probability_of_failure_next_7_days
- Métricas: AUC-ROC > 0.85

**Modelo 3: HOSCompliancePredictor (RandomForest)**
- Input: Historial conducción, ruta planificada, tráfico
- Output: probability_of_violation_next_2h
- Métricas: Precision > 0.90

**Modelo 4: OverweightRiskPredictor (XGBoost)**
- Input: Configuración vehículo, carga declarada, ruta, estado
- Output: probability_overweight, recommended_redistribution
- Métricas: AUC-ROC > 0.80

**Modelo 5: DemandForecaster (GradientBoosting)**
- Input: Región, mes, camiones activos, tráfico
- Output: predicted_demand
- Métricas: MAPE < 15%

**Modelo 6: OptimalLocationRecommender (K-Means + Gap Analysis)**
- Input: Estaciones existentes, densidad tráfico, demanda
- Output: recommended_locations
- Métrica: Silhouette Score > 0.6

**Archivos a generar:**
- `apps/analytics/models.py` (Prediction para guardar resultados)
- `apps/analytics/tire_wear_model.py`
- `apps/analytics/tire_failure_model.py`
- `apps/analytics/hos_predictor.py`
- `apps/analytics/overweight_predictor.py`
- `apps/analytics/demand_forecaster.py`
- `apps/analytics/location_optimizer.py`
- `apps/analytics/validators.py` (validate_prediction, validate_model_performance)
- `apps/analytics/training_manager.py` (entrena todos los modelos)
- `apps/analytics/management/commands/entrenar_modelos.py`
- `apps/analytics/management/commands/validar_predicciones.py`

**Al terminar:** Verificar que `python manage.py entrenar_modelos` funcione con datos simulados.

---

### 🔷 FASE 10: SIMULADOR IoT COMPLETO (60 min)

**Objetivo:** Crear el simulador que genera datos realistas para pruebas.

**Archivo:** `scripts/simulador_iot.py`

**Características:**
1. Simula 10 tractomulas con 18 sensores cada una (180 sensores)
2. Genera lecturas cada 30 segundos
3. Simula rutas reales por carreteras NHS
4. Inyecta escenarios automáticamente:
   - Min 0-10: Operación normal
   - Min 10-15: Desgaste gradual en FL-1 (baja presión 1 psi/h)
   - Min 15-16: Pinchazo súbito en RR-2 (caída 30 psi en 1 min)
   - Min 16-20: Sobrecalentamiento en RL-3 (temp sube a 180°F)
   - Min 20-25: Frenazos bruscos (acelerómetro -2G)
   - Min 25-30: Sensores offline (TL-2 sin comunicación)
   - Min 30-35: Violación HOS (conductor lleva 12h manejando)
   - Min 35-40: Overweight (peso excesivo en eje drive)
   - Repetir ciclo

**Reglas de generación realista:**
- Presión base: 100 psi ± 5 psi (varía por posición)
- Temperatura base: 110°F + (speed_mph * 0.2) + random(-5, 5)
- Vibración: 0.2G + (speed_mph * 0.005) + random(-0.1, 0.1)
- Correlación entre llantas del mismo eje
- Efecto de velocidad y carga

**Modos:**
- `python simulador_iot.py --modo demo` (10 tractomulas, ciclo 40 min)
- `python simulador_iot.py --modo stress --tractomulas 1000`
- `python simulador_iot.py --escenario pinchazo --tractomula TRK-001`

**Logs con colores:**
- 🟢 Normal
- 🟡 Warning
- 🔴 Critical

**Al terminar:** Verificar que el simulador envíe datos correctamente a la API y que se generen alertas.

---

### 🔷 FASE 11: DASHBOARDS WEB (12 PÁGINAS) (90 min)

**Objetivo:** Crear las 12 páginas web con Bootstrap 5 + Plotly + Leaflet.

**Templates base:**
- `templates/base.html` (Bootstrap 5 + navbar + sidebar + footer)
- `templates/includes/navbar.html`
- `templates/includes/sidebar.html`

**Las 12 páginas:**

1. **resumen.html** - KPIs globales + mapa flota en tiempo real
2. **monitoreo_iot.html** - Estado 180 sensores (WebSockets)
3. **alertas.html** - Lista, filtros, acknowledge/resolve
4. **hos_compliance.html** - Estado conductores, alertas HOS, violaciones
5. **desgaste_llantas.html** - Predicción por llanta, factores, vida restante
6. **peso_vehiculo.html** - Peso por eje, Federal Bridge, alertas overweight
7. **recomendaciones.html** - Sugerencias activas + historial
8. **geoespacial.html** - Heatmap de servicios
9. **estaciones_descanso.html** - PILOT/LOVES/TravelCenters
10. **combustible_reciclaje.html** - Sostenibilidad ambiental
11. **regulacion_seguridad.html** - WIM + regulaciones
12. **modelos_predictivos.html** - Predicciones ML + métricas

**Cada página debe tener:**
- Tarjetas KPI (Bootstrap cards)
- Gráficos Plotly interactivos ({{ fig|safe }})
- Mapa Leaflet con capas
- Tablas con DataTables.js
- Filtros dinámicos
- Actualización en tiempo real (WebSockets para páginas 2, 3, 4)

**Archivos:**
- `apps/dashboards/views.py` (12 vistas)
- `apps/dashboards/urls.py`
- `apps/dashboards/plotly_charts.py` (funciones para generar gráficos)
- `apps/dashboards/templatetags/custom_tags.py`
- `static/css/custom.css`
- `static/js/custom.js`
- `static/js/websockets.js`

**Al terminar:** Verificar que las 12 páginas carguen correctamente.

---

### 🔷 FASE 12: DATA INGESTION - ETL PARA 16 DATASETS (45 min)

**Objetivo:** Crear el ETL que carga los 16 datasets estáticos.

**Modelos:**
- `DataSource` (name, file_path, file_type, schema, last_load)
- `ETLJob` (dataset, status, records_processed, started_at, completed_at, error_log)

**Parsers (1 por cada dataset):**
1. NHSRoutesParser - NTAD_National_Highway_System_NHS_Routes.geojson
2. TruckStopParkingParser - NTAD_Truck_Stop_Parking.geojson
3. AltFuelStationsParser - alt_fuel_stations.csv
4. PilotLocationsParser - all_locations_plot.csv
5. LovesLocationsParser - LovesSearchResults.xlsx
6. TravelCentersParser - locmaster20260504_travel_center_priv.xlsx
7. TireShopsParser - tire_shops_usa_osm.csv
8. TruckTireCandidatesParser - truck_tire_candidates_usa_osm.csv
9. RecyclingParser - US_Recycling_Infrastructure_2022_EPA.csv
10. WIMStationsParser - NTAD_Weigh_in_Motion_Stations.csv
11. SizeWeightParser - Truck_Size_and_Weight_Enforcement_Data.csv
12. CompanyCensusParser - Company_Census_File_20260604.csv
13. MonthlyStatsParser - Monthly_Transportation_Statistics_20260604.csv
14. POIsParser - pois_corredores_eeuu.csv/.geojson
15. EPADisasterParser - EPA_Disaster_Debris_Recovery_Data.csv
16. FederalRegsParser - Datos federales HOS + peso + tread depth

**Pipeline ETL:**
1. Validación de schema
2. Limpieza (nulos, duplicados, formatos)
3. Transformación geoespacial (crear PointField)
4. Carga con bulk_create
5. Registro en ETLJob

**Comando:** `python manage.py cargar_datos_csv`

**Al terminar:** Verificar que los 16 datasets se carguen correctamente.

---

### 🔷 FASE 13: API REST UNIFICADA + DOCUMENTACIÓN (30 min)

**Objetivo:** Crear la API REST unificada con documentación OpenAPI.

**Archivos:**
- `apps/api/__init__.py`
- `apps/api/urls.py` (URLs unificadas)
- `apps/api/views.py` (vista raíz con lista de endpoints)

**Endpoints críticos:**
- `POST /api/iot/reading/` - Recibir datos IoT
- `GET /api/devices/` - Lista dispositivos
- `GET /api/alerts/` - Alertas activas
- `GET /api/recommendations/?device_id=X` - Recomendaciones
- `GET /api/hos/?driver_id=X` - Estado HOS
- `GET /api/weight/?truck_id=X` - Estado peso
- `GET /api/tires/wear-prediction/?sensor_id=X` - Predicción desgaste
- `GET /api/predictions/tire-failure/?device_id=X` - Predicción fallo

**Documentación:**
- drf-spectacular en `/api/docs/`
- Schema en `/api/schema/`

**Al terminar:** Verificar que `/api/docs/` muestre Swagger UI.

---

### 🔷 FASE 14: DOCUMENTACIÓN TÉCNICA (8 ARCHIVOS) (60 min)

**Objetivo:** Crear la documentación que cumple las 4 fases del reto.

**Archivos en docs/:**

1. **METODOLOGIA.md** (FASE 1 del reto - 20h)
   - Metodología de identificación de fuentes
   - Catálogos de datos
   - Formatos estandarizados
   - Métodos de captura
   - Enfoque general de análisis

2. **ARQUITECTURA.md** (FASE 2 del reto - 30h)
   - Metodología de almacenamiento
   - Evaluación comparativa de herramientas
   - Flujo conceptual de datos
   - Herramientas Big Data
   - Criterios de calidad

3. **ANALISIS_PREDICTIVO.md** (FASE 3 del reto - 40h)
   - Técnicas de análisis descriptivo
   - Propuesta metodológica predictiva (6 modelos ML)
   - Criterios de validación
   - Diseño de visualizaciones
   - Evaluación de herramientas

4. **REGULACIONES_FEDERALES.md** (Específico del proyecto)
   - HOS FMCSA 49 CFR Part 395
   - Profundidad mínima FMCSA 49 CFR 393.75
   - Federal Bridge Formula 23 CFR 658.17
   - Cómo el sistema cumple cada regulación

5. **FORMULA_DESGASTE.md** (Específico del proyecto)
   - Fórmula completa de predicción de desgaste
   - Los 10 factores de ajuste
   - Ejemplos de cálculo
   - Validación con datos reales

6. **SIMULACION.md** (Específico del proyecto)
   - Arquitectura del simulador
   - Escenarios de prueba
   - Reglas de generación realista
   - Cómo ejecutar el simulador

7. **INTEGRACION.md** (FASE 4 del reto - 36h parcial)
   - Proceso global de integración
   - Evaluación del sistema
   - Fortalezas y limitaciones

8. **PLAN_MEJORA.md** (FASE 4 del reto - 36h parcial)
   - Plan de continuidad
   - Mantenimiento
   - Actualizaciones futuras
   - Nuevas funcionalidades

**Al terminar:** Verificar que los 8 documentos estén completos y alineados con el reto.

---

### 🔷 FASE 15: COMANDOS DE GESTIÓN Y SCRIPTS FINALES (30 min)

**Objetivo:** Crear los comandos de gestión y scripts finales.

**Comandos:**
1. `python manage.py inspect_existing_db`
2. `python manage.py cargar_datos_csv`
3. `python manage.py cargar_regulaciones_federales`
4. `python manage.py simular_datos_iot`
5. `python manage.py entrenar_modelos`
6. `python manage.py validar_predicciones`
7. `python manage.py generar_reporte`

**Scripts:**
- `scripts/seed_data.py` - Crea datos iniciales (conductores, camiones, dispositivos)
- `scripts/test_endpoints.py` - Prueba todos los endpoints de la API
- `scripts/backup_db.py` - Backup de la base de datos

**Al terminar:** Verificar que los 7 comandos funcionen.

---

## ✅ CHECKLIST FINAL DE VERIFICACIÓN

Antes de dar el proyecto por terminado, verificar:

### 📦 Instalación:
- [ ] `pip install -r requirements.txt` funciona
- [ ] `python manage.py migrate` crea todas las tablas
- [ ] `python manage.py createsuperuser` crea admin
- [ ] `python manage.py runserver` inicia sin errores

### 📊 Datos:
- [ ] Los 16 datasets se cargan con `cargar_datos_csv`
- [ ] Las regulaciones federales se cargan
- [ ] El simulador genera datos realistas
- [ ] Se crean 10 tractomulas con 18 sensores cada una

### 🧠 ML:
- [ ] Los 6 modelos se entrenan
- [ ] Las predicciones son coherentes
- [ ] Los modelos se guardan en ml_models/

### 🌐 Web:
- [ ] Las 12 páginas cargan
- [ ] Los mapas Leaflet funcionan
- [ ] Los gráficos Plotly se renderizan
- [ ] Los WebSockets actualizan en tiempo real

### 🔌 API:
- [ ] POST /api/iot/reading/ funciona
- [ ] La documentación Swagger se muestra
- [ ] Los filtros geoespaciales funcionan
- [ ] La paginación funciona

### 📚 Documentación:
- [ ] Los 8 documentos están completos
- [ ] README.md tiene instrucciones claras
- [ ] El código tiene docstrings
- [ ] Las 4 fases del reto están cubiertas

---

## 🚀 COMANDOS PARA PROBAR EL SISTEMA

```bash
# 1. Crear entorno virtual
cd pin_platform
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env con credenciales de PostgreSQL

# 4. Migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Cargar datos estáticos
python manage.py cargar_datos_csv
python manage.py cargar_regulaciones_federales

# 7. Crear datos iniciales
python scripts/seed_data.py

# 8. Entrenar modelos ML
python manage.py entrenar_modelos

# 9. Iniciar servidor Django
python manage.py runserver

# 10. En OTRA terminal, iniciar simulador
python scripts/simulador_iot.py --modo demo

# 11. Abrir navegador
# http://localhost:8000/ (Dashboard)
# http://localhost:8000/admin/ (Admin)
# http://localhost:8000/api/docs/ (API Docs)
```

---

## 📞 CRITERIOS DE ACEPTACIÓN

El proyecto se considera COMPLETO cuando:

✅ Cumple las 4 fases del reto (126 horas)
✅ Tiene 20+ modelos Django funcionales
✅ Tiene 6 modelos ML entrenados y validados
✅ Tiene 12 dashboards web interactivos
✅ Tiene simulador IoT funcional con escenarios
✅ Cumple regulaciones FMCSA (HOS + tread depth + peso)
✅ Implementa fórmula de desgaste con 10 factores
✅ Tiene API REST documentada con OpenAPI
✅ Tiene 8 documentos técnicos completos
✅ Se puede ejecutar con `python manage.py runserver`

---

## 🎯 INSTRUCCIONES FINALES PARA LA IA

**COMIENZA AHORA con la FASE 1.** Genera todos los archivos de la estructura base y configuración. Cuando termines la FASE 1, espera mi confirmación antes de continuar con la FASE 2.

**IMPORTANTE:**
- No te saltes ninguna fase
- No omitas ningún archivo
- No dejes código a medias
- Si un archivo es muy largo, divídelo en partes
- Al final de cada fase, indica cómo probar lo generado
