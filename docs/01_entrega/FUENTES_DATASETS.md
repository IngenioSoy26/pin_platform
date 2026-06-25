# Fuentes de Datasets (Descarga y Citacion)

## 1. Proposito

Este documento consolida, en un solo lugar, las fuentes oficiales y paginas de referencia para los datasets usados en PIN Platform. Esta informacion se usa tanto para:

- justificar el origen de datos en la memoria academica;
- permitir que un tercero vuelva a descargar los datasets;
- dejar trazabilidad clara de portales oficiales y sitios corporativos.

Se complementa con el documento de trabajo: `c:\Users\gusta\Desktop\Maestria\0.1. Practicas\INFORME BD\De donde descargar los dataset.docx`.

## 2. Portales oficiales y APIs

### 2.1 USDOT / BTS GeoData (NTAD)

- Portal: https://geodata.bts.gov/
- National Highway System (NHS): https://geodata.bts.gov/datasets/usdot::national-highway-system-nhs/about
- Truck Stop Parking: https://geodata.bts.gov/datasets/usdot::truck-stop-parking/about
- Weigh-in-Motion Stations (WIM): si el enlace directo cambia, usar busqueda en el portal: https://geodata.bts.gov/search?collection=dataset&q=weigh-in-motion

Uso: rutas/corredores NHS, apoyo operacional (parking y WIM), base para demo de flota y analitica geoespacial.

### 2.2 FHWA / HPMS

- Dataset en catalog.data.gov: https://catalog.data.gov/dataset/highway-performance-monitoring-system-hpms
- Pagina FHWA HPMS: https://www.fhwa.dot.gov/policyinformation/hpms.cfm

Uso: contexto de estado de vias y endpoints/servicios por estado. En la plataforma, la capa de rugosidad se implementa via endpoints GeoJSON y fallbacks cuando no hay geometria completa en BD.

### 2.3 FMCSA / Company Census (MCMIS)

- Dataset oficial: https://data.transportation.gov/Trucking-and-Motorcoaches/Company-Census-File/az4n-8mr2
- SAFER (consulta de carrier): https://safer.fmcsa.dot.gov/

Uso: informacion de carriers/empresas, variables MCS-150 y metadatos de operacion.

### 2.4 BTS / Monthly Transportation Statistics

- Pagina oficial: https://www.bts.gov/monthly-transportation-statistics

Uso: contexto macro de estadisticas de transporte para analitica y dashboards.

### 2.5 FHWA / Truck Size and Weight Enforcement Data

- Dataset oficial: https://catalog.data.gov/dataset/truck-size-and-weight-enforcement-data

Uso: enforcement, conteos de pesaje, violaciones y permisos por estado.

### 2.6 DOE / AFDC Alternative Fuel Stations

- Portal de estaciones: https://afdc.energy.gov/stations/

Uso: estaciones de combustible alternativo (CNG, LNG, EV, etc.) para cobertura operacional y analitica geoespacial.

### 2.7 EPA / Reciclaje e infraestructura ambiental

- US Recycling Infrastructure Map: https://www.epa.gov/infrastructure/us-recycling-infrastructure-map
- Disaster Debris Recovery Tool / Debris Recovery Map: https://www.epa.gov/debris-recovery-map

Uso: capas de soporte ambiental y sitios de recuperacion/reciclaje, integrados como amenidades complementarias.

### 2.8 NOAA / NWS (clima y alertas)

- Documentacion oficial NWS API: https://www.weather.gov/documentation/services-web-api
- Base URL: https://api.weather.gov

Uso: alertas meteorologicas activas y contexto operativo (clima) en el dashboard geoespacial.

## 3. Fuentes corporativas (locators)

Estas fuentes se basan en portales de ubicaciones publicas, utiles para obtener una red de travel centers y servicios operativos.

- Love's: https://www.loves.com/location-and-fuel-price-search
- TravelCenters of America / Petro: https://www.ta-petro.com/location/
- Pilot Flying J: https://locations.pilotflyingj.com/search

Uso: amenidades operativas (descanso, combustible, parqueo, duchas, restaurantes, etc.) para cobertura por corredor.

## 4. OpenStreetMap (OSM)

Para talleres y puntos candidatos:

- OpenStreetMap: https://www.openstreetmap.org/
- Overpass Turbo (extraccion por consultas): https://overpass-turbo.eu/

Uso: talleres de llantas y candidatos de servicio con georreferenciacion.

## 5. Tabla resumen por archivo

| Archivo (data/) | Fuente recomendada |
|---|---|
| `NTAD_National_Highway_System_-*.geojson` | BTS GeoData NTAD - NHS |
| `NTAD_Truck_Stop_Parking_*.csv` | BTS GeoData NTAD - Truck Stop Parking |
| `NTAD_Weigh_in_Motion_Stations_*.csv` | BTS GeoData NTAD - Weigh-in-Motion Stations |
| `Highway_Performance_Monitoring_System__HPMS_.csv` | catalog.data.gov - HPMS |
| `Company_Census_File_*.csv` | data.transportation.gov - FMCSA Company Census |
| `Truck_Size_and_Weight_Enforcement_Data.csv` | catalog.data.gov - Truck Size and Weight Enforcement |
| `Monthly_Transportation_Statistics_*.csv` | BTS - Monthly Transportation Statistics |
| `alt_fuel_stations (*.csv)` | DOE - AFDC |
| `US_Recycling_Infrastructure_*.csv` | EPA - Recycling Infrastructure Map |
| `EPA_Disaster_Debris_Recovery_Data_*.csv` | EPA - Debris Recovery Map |
| `*_osm.csv` | OpenStreetMap / Overpass |
| `LovesSearchResults.xlsx` | Love's location search |
| `locmaster*_travel_center_priv.xlsx` | TA / Petro location search |
| `all_locations_plot.csv` | Pilot Flying J location search |

## 6. Notas de citacion

- Para datasets federales (USDOT/FHWA/FMCSA/BTS/EPA/DOE/NOAA), citar la pagina oficial del portal o dataset.
- Para fuentes corporativas, citar la pagina de busqueda/locator y, si aplica, aclarar que los datos se usan solo con proposito academico (sin redistribucion comercial).
- Para OSM, citar OpenStreetMap y Overpass, y mencionar que la licencia de OSM requiere atribucion.
