# Metodologia de Captura y Analisis Inicial

## Objetivo

Definir el enfoque metodologico para capturar, organizar y analizar la informacion que alimentara la plataforma PIN, alineando los 16 datasets estaticos con el sistema IoT final para tractomulas.

## Fuentes criticas identificadas

1. Infraestructura vial y corredores: rutas NHS, corredores y puntos de interes.
2. Servicios operativos: truck stops, fuel, travel centers, talleres de llantas y reciclaje.
3. Regulacion y cumplimiento: estaciones WIM, enforcement estatal, HOS y limites federales.
4. Contexto empresarial y estadistico: carriers FMCSA y estadisticas BTS.
5. Telemetria futura: dispositivo maestro, 18 sensores de llantas, eventos de conduccion y peso.

## Criterios de captura

- Estandarizar nombres de campos, tipos de dato y unidades de medida.
- Conservar trazabilidad de la fuente original por dataset y fecha de carga.
- Separar claramente datos geoespaciales, catalogos operativos, regulaciones y analitica.
- Preparar el modelo para integracion posterior con lecturas IoT en tiempo real.

## Clasificacion de los 16 datasets

### Geoespaciales

- `NTAD_National_Highway_System_-2908344783259962276.geojson`
- `pois_corredores_eeuu.geojson`
- `pois_corredores_eeuu.csv`

### Servicios y estaciones

- `NTAD_Truck_Stop_Parking_3144670861174225213.csv`
- `alt_fuel_stations (Apr 19 2026).csv`
- `all_locations_plot.csv`
- `LovesSearchResults (1).xlsx`
- `locmaster20260504_travel_center_priv.xlsx`
- `tire_shops_usa_osm.csv`
- `truck_tire_candidates_usa_osm.csv`
- `US_Recycling_Infrastructure_2022_-7015395891470271269.csv`

### Regulacion y control

- `NTAD_Weigh_in_Motion_Stations_1665357467742259787.csv`
- `Truck_Size_and_Weight_Enforcement_Data.csv`

### Contexto sectorial

- `Company_Census_File_20260604.csv`
- `Monthly_Transportation_Statistics_20260604.csv`
- `EPA_Disaster_Debris_Recovery_Data_903120106498694009.csv`

## Enfoque de analisis inicial

- Analisis descriptivo para cobertura geografica, densidad de servicios y vacios operativos.
- Preparacion para analisis predictivo sobre desgaste de llantas, demanda de servicios y riesgo operativo.
- Integracion futura con reglas HOS, monitoreo de peso y alertas de mantenimiento.

## Resultado esperado de Fase 1

- Proyecto Django con estructura estable.
- Configuracion lista para evolucionar a PostGIS y canales en tiempo real.
- Base documental inicial para justificar las decisiones de ingesta y modelado.
