# Anexo E. Tabla de Datasets (Origen, Descarga, Licencia y Atribucion)

## Proposito

Este anexo documenta cada archivo presente en `pin_platform/data/` indicando:

- nombre del archivo local;
- uso dentro de PIN Platform;
- fuente y URL de descarga o portal oficial;
- fecha de descarga (si se puede inferir por el nombre del archivo o si se registró);
- licencia o atribucion requerida.

Cuando no existe evidencia local de la fecha de descarga, se deja como `N/D` y se recomienda registrar ese dato en la entrega final.

## Tabla consolidada

| Archivo local (`data/`) | Uso en PIN Platform | Fuente | URL de referencia (descarga / portal) | Fecha de descarga | Licencia / atribucion |
|---|---|---|---|---|---|
| `NTAD_National_Highway_System_-2908344783259962276.geojson` | Rutas NHS, corredores, base de rutas demo y capas geoespaciales | USDOT / BTS GeoData (NTAD) | https://geodata.bts.gov/datasets/usdot::national-highway-system-nhs/about | N/D | Datos federales; citar el portal BTS/NTAD y atribuir fuente |
| `NTAD_Truck_Stop_Parking_3144670861174225213.csv` | Truck stops/parking y servicios asociados | USDOT / BTS GeoData (NTAD) | https://geodata.bts.gov/datasets/usdot::truck-stop-parking/about | N/D | Datos federales; citar el portal BTS/NTAD y atribuir fuente |
| `NTAD_Weigh_in_Motion_Stations_1665357467742259787.csv` | Estaciones WIM (pesaje en movimiento) | USDOT / BTS GeoData (NTAD) | https://geodata.bts.gov/search?collection=dataset&q=weigh-in-motion | N/D | Datos federales; citar el portal BTS/NTAD y atribuir fuente |
| `Highway_Performance_Monitoring_System__HPMS_.csv` | Inventario HPMS por estado y endpoints; base para estado de vias/rugosidad | FHWA (referenciado desde catalog.data.gov) | https://catalog.data.gov/dataset/highway-performance-monitoring-system-hpms | N/D | Datos federales; citar FHWA/catalog.data.gov |
| `Truck_Size_and_Weight_Enforcement_Data.csv` | Enforcement de peso/tamaño: pesajes, violaciones, permisos por estado | FHWA (data.transportation.gov / catalog.data.gov) | https://catalog.data.gov/dataset/truck-size-and-weight-enforcement-data | N/D | Datos federales; citar FHWA/catalog.data.gov |
| `Monthly_Transportation_Statistics_20260604.csv` | Indicadores macro de transporte para analitica y contexto | BTS | https://www.bts.gov/monthly-transportation-statistics | 2026-06-04 (por nombre) | Datos federales; citar BTS |
| `Company_Census_File_20260604.csv` | Carriers/empresas (MCMIS / MCS-150), contexto de flota y carriers | FMCSA MCMIS (data.transportation.gov) | https://data.transportation.gov/Trucking-and-Motorcoaches/Company-Census-File/az4n-8mr2 | 2026-06-04 (por nombre) | Datos federales; citar FMCSA/data.transportation.gov |
| `alt_fuel_stations (Apr 19 2026).csv` | Estaciones de combustible alternativo (CNG/LNG/EV) para cobertura operacional | U.S. DOE AFDC | https://afdc.energy.gov/stations/ | 2026-04-19 (por nombre) | Fuente gubernamental; citar AFDC/DOE |
| `US_Recycling_Infrastructure_2022_-7015395891470271269.csv` | Infraestructura de reciclaje (incluye tires) como capa de apoyo | EPA | https://www.epa.gov/infrastructure/us-recycling-infrastructure-map | 2022 (por nombre) | Fuente gubernamental; citar EPA |
| `EPA_Disaster_Debris_Recovery_Data_903120106498694009.csv` | Sitios de recovery/landfill/recycling para planeacion de contingencias | EPA | https://www.epa.gov/debris-recovery-map | N/D | Fuente gubernamental; citar EPA |
| `all_locations_plot.csv` | Travel centers (cadena corporativa) para amenidades operativas | Pilot Flying J | https://locations.pilotflyingj.com/search | N/D | Fuente corporativa; citar el portal. Uso academico; evitar redistribucion comercial |
| `LovesSearchResults.xlsx` | Travel stops Love’s y precios/ubicaciones | Love’s Travel Stops | https://www.loves.com/location-and-fuel-price-search | N/D | Fuente corporativa; citar el portal. Uso academico; evitar redistribucion comercial |
| `locmaster20260504_travel_center_priv.xlsx` | Travel centers TA/Petro | TravelCenters of America / Petro | https://www.ta-petro.com/location/ | 2026-05-04 (por nombre) | Fuente corporativa; citar el portal. Uso academico; evitar redistribucion comercial |
| `tire_shops_usa_osm.csv` | Talleres/servicios de llantas para cobertura operacional | OpenStreetMap | https://www.openstreetmap.org/ | N/D | ODbL: requiere atribucion a OpenStreetMap contributors |
| `truck_tire_candidates_usa_osm.csv` | Candidatos a servicio de llantas (OSM/Overpass) | OpenStreetMap / Overpass | https://overpass-turbo.eu/ | N/D | ODbL: requiere atribucion a OpenStreetMap contributors |

## Notas de entrega recomendadas

- Para fuentes federales, citar el portal y el dataset. En la entrega, incluir la fecha de acceso y, si aplica, la fecha de última actualización del dataset (según el portal).
- Para OSM, incluir siempre atribución visible: `© OpenStreetMap contributors` y mencionar la licencia ODbL.
- Para fuentes corporativas, declarar uso academico y no redistribuir datos sin revisar terminos del sitio.
