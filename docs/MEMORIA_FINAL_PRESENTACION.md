# Memoria Final de Presentacion

## PIN Platform

Plataforma web IoT + Big Data para monitoreo de tractomulas, llantas, cumplimiento normativo, rutas, amenidades operativas y analitica geoespacial aplicada al transporte de carga en Estados Unidos.

## 1. Portada Sugerida

- Titulo del trabajo: `PIN Platform: sistema integrado de analisis y visualizacion de datos masivos para monitoreo operativo de tractomulas`
- Autor: `Gustavo Alonzo Segrera Gomez`
- Programa: `Maestria en Big Data`
- Entidad vinculada al reto: `Ambientronika Ltda`
- Universidad: `UNIR`
- Fecha de entrega: completar en la version final

### Imagen sugerida

- `Figura 1. Portada conceptual del proyecto`
- Contenido recomendado: captura del dashboard principal o del mapa operativo con tractomulas y capas activas.
- Ubicacion: portada o primera pagina despues del titulo.

## 2. Resumen Ejecutivo

PIN Platform es una solucion digital orientada a transformar datos operativos, geoespaciales e IoT en informacion accionable para la supervision de tractomulas. La plataforma integra el monitoreo de llantas, el estado de la flota, el cumplimiento HOS, el control de peso, la cobertura de servicios, el contexto de rutas y las condiciones del entorno en una misma experiencia web.

El proyecto responde a la necesidad de centralizar multiples fuentes de datos que normalmente se encuentran dispersas: sensores, rutas, estaciones de apoyo, informacion regulatoria, condiciones meteorologicas y datasets de transporte. Para ello se implemento una arquitectura modular basada en Django, con dashboards interactivos, mapas Leaflet, procesos ETL y una API de ingesta IoT.

El sistema ya permite visualizar flota demo/live sobre rutas, telemetria historica y operativa, amenidades por corredor, clima y cierres, asi como una capa tematica de rugosidad de carretera. Aunque todavia existen componentes por cerrar formalmente, la plataforma ya es funcional, demostrable y defendible academicamente.

### Imagen sugerida

- `Figura 2. Vista general del ecosistema PIN Platform`
- Contenido recomendado: collage de `dashboard/`, `dashboards/resumen/`, `dashboards/iot/` y `dashboards/geoespacial/`.
- Ubicacion: al final del resumen o inicio de la introduccion.

## 3. Contexto del Reto

De acuerdo con la ficha de reto aprobada, el proyecto PIN fue planteado como un proceso de analisis y visualizacion de datos masivos derivados de la operacion del sistema de estaciones de descanso y del monitoreo de llantas, con el objetivo de generar informacion accionable para optimizar decisiones y mejorar el rendimiento del sistema.

La ficha de reto indica como objetivo general:

> Disenar e implementar un proceso de analisis y visualizacion de datos masivos derivados de la operacion del sistema de estaciones de descanso y el monitoreo de llantas, para generar informacion accionable que optimice la toma de decisiones y el rendimiento del sistema.

La misma ficha organiza el trabajo en cuatro grandes fases:

- `Fase 1 (20 h)`: metodologia de captura y analisis inicial.
- `Fase 2 (30 h)`: diseno del sistema de captura, almacenamiento y procesado.
- `Fase 3 (40 h)`: diseno de tecnicas analiticas y visualizaciones.
- `Fase 4 (36 h)`: integracion, evaluacion y presentacion final.

La duracion total documentada es de `126 horas`, lo cual coincide con la estructura academica del reto y con la necesidad de producir no solo software, sino tambien metodologia, arquitectura, analitica, evaluacion y documentacion final.

### Imagen sugerida

- `Figura 3. Esquema de fases del reto`
- Contenido recomendado: una tabla o diagrama con las 4 fases y sus horas.
- Ubicacion: inmediatamente despues de esta seccion.

## 4. Problema y Justificacion

La operacion de tractomulas implica la convivencia de multiples variables criticas:

- presion, temperatura y vibracion de llantas;
- desgaste progresivo y riesgo de falla;
- cumplimiento de HOS;
- control del peso vehicular;
- acceso a servicios de apoyo en ruta;
- visibilidad sobre rutas, cierres y clima;
- necesidad de integrar datos historicos y datos casi en tiempo real.

En escenarios reales, esta informacion suele estar fragmentada en hojas de calculo, plataformas aisladas o procesos manuales. Esa fragmentacion reduce la capacidad de anticipar fallos, priorizar mantenimiento y tomar decisiones proactivas durante la operacion.

PIN Platform se justifica como una propuesta de integracion de datos masivos, analitica y visualizacion en un unico sistema, con valor tanto academico como operacional.

## 5. Objetivos del Proyecto

### 5.1 Objetivo General

Desarrollar una plataforma web integrada que combine IoT, Big Data, visualizacion geoespacial y analitica para monitorear tractomulas, llantas, cumplimiento normativo y contexto operacional de rutas en EE.UU.

### 5.2 Objetivos Especificos

- modelar tractomulas, dispositivos maestros, sensores y lecturas de llanta;
- incorporar reglas HOS y control de peso en la logica de supervision;
- construir un proceso ETL para datasets operativos y geoespaciales;
- exponer dashboards y mapas interactivos;
- habilitar una API de ingesta IoT;
- establecer una base para analitica predictiva y recomendaciones;
- dejar documentado el sistema para presentacion, continuidad y mejora.

## 6. Metodologia de Trabajo Alineada al Reto

### 6.1 Fase 1. Metodologias de captura y analisis inicial

En esta fase se identificaron los dominios de datos criticos:

- telemetria y sensores;
- rutas y corredores;
- servicios y amenidades;
- regulacion y enforcement;
- estadisticas sectoriales.

Tambien se definieron criterios de calidad, estructura y trazabilidad para los datasets.

### 6.2 Fase 2. Captura, almacenamiento y procesado

Se diseno y construyo la estructura modular del proyecto, junto con el modelo de almacenamiento en apps Django y los procesos ETL para integrar datos externos.

### 6.3 Fase 3. Tecnicas analiticas y visualizaciones

Se definieron dashboards, mapas, KPIs, logicas de simulacion, reglas de alerta y bases para modelos predictivos.

### 6.4 Fase 4. Integracion, evaluacion y presentacion final

Se integraron ETL, mapas, dashboards e ingesta IoT, y se genero la presente documentacion como soporte de cierre y presentacion del sistema.

### Imagen sugerida

- `Figura 4. Flujo metodologico del proyecto`
- Contenido recomendado: diagrama con captura -> ETL -> almacenamiento -> analitica -> visualizacion -> decision.
- Ubicacion: al final de esta seccion.

## 7. Arquitectura de la Solucion

PIN Platform sigue una arquitectura modular sobre Django.

### 7.1 Capa de presentacion

- templates Django;
- Bootstrap;
- Plotly;
- Leaflet;
- consumo de APIs JSON para actualizacion live.

### 7.2 Capa de aplicacion

- vistas Django y DRF;
- servicios por dominio;
- motores de alerta y recomendacion;
- comandos de gestion.

### 7.3 Capa de datos

- modelos relacionales;
- ETL para CSV, XLSX y GeoJSON;
- almacenamiento actual funcional;
- evolucion recomendada a PostgreSQL + PostGIS para cierre geoespacial robusto.

### 7.4 Apps principales

- `core`
- `devices`
- `tires`
- `hos_monitoring`
- `weight_monitoring`
- `alerts`
- `recommendations`
- `iot_ingestion`
- `routes`
- `stations`
- `fuel_alternative`
- `recycling`
- `regulation`
- `carriers`
- `analytics`
- `dashboards`
- `data_ingestion`

### Imagen sugerida

- `Figura 5. Arquitectura funcional de PIN Platform`
- Contenido recomendado: diagrama por capas y apps.
- Ubicacion: despues de esta seccion.

## 8. Modelo de Datos y Base de Datos

La base de datos documenta entidades de infraestructura, flota, telemetria, cumplimiento, alertas, recomendaciones y analitica. El documento de base de datos entregado y el ERD suministrado muestran que la estructura cubre ubicaciones, truck stops, estaciones de combustible alternativo, talleres, rutas, llantas, conductores, inspecciones, alertas, recomendaciones y predicciones.

Este punto es especialmente importante porque la integracion del sistema no depende de una sola tabla central, sino de la relacion entre entidades de soporte operacional, contexto geoespacial, telemetria y cumplimiento.

### Imagen obligatoria sugerida

- `Figura 6. Diagrama entidad-relacion de PIN Platform`
- Archivo recomendado: `c:\Users\gusta\Desktop\Maestria\0.1. Practicas\INFORME BD\ER PIN.png`
- Ubicacion: justo en esta seccion.
- Pie de figura sugerido: `Modelo entidad-relacion del sistema PIN Platform, incluyendo infraestructura, flota, telemetria, cumplimiento, alertas, recomendaciones y analitica.`

## 9. Fuentes de Datos y Origen de los Datasets

Los datasets integrados en la plataforma provienen de portales publicos, fuentes corporativas, catalogos operativos y extracciones geoespaciales. En la tabla siguiente se documenta el origen recomendado a citar en la memoria.

> Nota: en algunos casos el archivo original ya estaba descargado en el proyecto y no conserva en el nombre la URL exacta de descarga. Para la memoria se recomienda citar el portal oficial o pagina de origen desde la cual se obtuvo o pudo obtenerse el dataset.
>
> Complemento: se usaron URLs de referencia del documento `De donde descargar los dataset.docx` para consolidar fuentes clave (BTS GeoData/NTAD y portales corporativos).

| Archivo en `data/` | Uso en el sistema | Fuente/portal de origen | Pagina o sitio a citar |
|---|---|---|---|
| `NTAD_National_Highway_System_-2908344783259962276.geojson` | rutas NHS, corredores y flota demo | USDOT / BTS GeoData (NTAD) | `https://geodata.bts.gov/datasets/usdot::national-highway-system-nhs/about` |
| `NTAD_Truck_Stop_Parking_3144670861174225213.csv` | truck stop parking y servicios | USDOT / BTS GeoData (NTAD) | `https://geodata.bts.gov/datasets/usdot::truck-stop-parking/about` |
| `NTAD_Weigh_in_Motion_Stations_1665357467742259787.csv` | estaciones WIM | USDOT / BTS GeoData (NTAD) | `https://geodata.bts.gov/search?collection=dataset&q=weigh-in-motion` |
| `Highway_Performance_Monitoring_System__HPMS_.csv` | inventario HPMS por estado y endpoints | catalog.data.gov / FHWA | `https://catalog.data.gov/dataset/highway-performance-monitoring-system-hpms` |
| `alt_fuel_stations (Apr 19 2026).csv` | combustible alternativo y estaciones | U.S. Department of Energy - AFDC | `https://afdc.energy.gov/stations/` |
| `all_locations_plot.csv` | ubicaciones corporativas de apoyo | Pilot Flying J | `https://locations.pilotflyingj.com/search` |
| `LovesSearchResults.xlsx` | paradas y servicios Love's | Love's Travel Stops | `https://www.loves.com/location-and-fuel-price-search` |
| `locmaster20260504_travel_center_priv.xlsx` | travel centers y servicios | TravelCenters of America / Petro | `https://www.ta-petro.com/location/` |
| `tire_shops_usa_osm.csv` | talleres de llantas | OpenStreetMap | `https://www.openstreetmap.org/` |
| `truck_tire_candidates_usa_osm.csv` | candidatos a servicio para llantas | OpenStreetMap / Overpass | `https://overpass-turbo.eu/` |
| `US_Recycling_Infrastructure_2022_-7015395891470271269.csv` | reciclaje e infraestructura ambiental | EPA | `https://www.epa.gov/infrastructure/us-recycling-infrastructure-map` |
| `EPA_Disaster_Debris_Recovery_Data_903120106498694009.csv` | soporte ambiental (debris recovery) | EPA | `https://www.epa.gov/debris-recovery-map` |
| `Truck_Size_and_Weight_Enforcement_Data.csv` | enforcement y control de peso | FHWA / data.transportation.gov | `https://catalog.data.gov/dataset/truck-size-and-weight-enforcement-data` |
| `Company_Census_File_20260604.csv` | empresas y carriers (MCMIS/MCS-150) | FMCSA MCMIS / data.transportation.gov | `https://data.transportation.gov/Trucking-and-Motorcoaches/Company-Census-File/az4n-8mr2` |
| `Monthly_Transportation_Statistics_20260604.csv` | contexto estadistico de transporte | Bureau of Transportation Statistics | `https://www.bts.gov/monthly-transportation-statistics` |

### Imagen sugerida

- `Figura 7. Mapa de fuentes de datos del proyecto`
- Contenido recomendado: esquema que agrupe fuentes en `USDOT/BTS`, `FHWA`, `FMCSA`, `DOE`, `EPA`, `OpenStreetMap`, `fuentes corporativas`.
- Ubicacion: al final de esta seccion.

## 10. Implementacion Tecnica Realizada

### 10.1 ETL y procesamiento

Se implemento un ETL con mejoras importantes:

- procesamiento por streaming;
- reduccion de consumo de memoria;
- seguimiento de `records_processed`;
- panel de ejecucion y estado live.

### 10.2 Dashboard principal y mapa de resumen

Se unifico la logica live de flota para evitar inconsistencias entre mapas y dashboards, y se incorporaron etiquetas sobre vehiculos, rutas y tramos recorridos.

### 10.3 Dashboard IoT

Se corrigio la visualizacion de telemetria historica y se dejo soporte para fallback cuando existen lecturas historicas pero no datos recientes en una ventana corta.

### 10.4 Dashboard geoespacial

Se construyo una vista de soporte operacional con:

- amenidades por corredor;
- hubs favorables;
- clima online;
- cierres operativos;
- filtros por categorias;
- limpieza visual por agrupamiento.

### 10.5 Mapa operativo

Se agrego una capa tematica de rugosidad con gradiente rojo, desacoplada de la flota y soportada por endpoint GeoJSON.

### Imagen sugerida

- `Figura 8. Dashboard ETL con progreso`
- `Figura 9. Dashboard de resumen con flota sobre rutas`
- `Figura 10. Dashboard IoT y sensores criticos`
- `Figura 11. Dashboard geoespacial con amenidades, clima y cierres`
- `Figura 12. Mapa operativo con capa de rugosidad`

## 11. API, Integracion IoT y Analitica

La API de ingesta IoT ya permite registrar lecturas del vehiculo y de las llantas, actualizar el estado del dispositivo maestro, generar alertas y disparar recomendaciones.

Adicionalmente, existe una capa de analitica estructural con soporte para:

- desgaste de llanta;
- probabilidad de falla;
- riesgo HOS;
- riesgo de sobrepeso;
- pronostico de demanda;
- optimizacion de ubicacion.

No obstante, para presentacion rigurosa debe aclararse que la estructura ML existe, pero que la validacion formal con metricas reales sigue siendo un pendiente de cierre.

### Imagen sugerida

- `Figura 13. Flujo de ingesta IoT`
- Contenido recomendado: payload -> API -> VehicleReading/TireReading -> AlertEngine -> RecommendationEngine.

## 12. Resultados y Valor Obtenido

Los principales resultados del proyecto son:

- plataforma funcional con multiples vistas y mapas;
- integracion de sensores, datos operativos y geoespaciales;
- soporte para toma de decisiones en rutas;
- mejora de trazabilidad del ETL;
- base tecnica para evolucion a una plataforma mas robusta.

El valor diferencial de PIN Platform radica en que no solo muestra telemetria, sino que la conecta con contexto operativo real o sinteticamente util.

## 13. Limitaciones y Aspectos por Cerrar

- algunas capas geoespaciales todavia dependen de datos sinteticos controlados;
- la capa HPMS no esta completamente poblada con geometria real para todos los casos;
- la validacion final de ML no esta cerrada con evidencia de metricas;
- la API REST unificada aun requiere cierre documental completo;
- el simulador IoT extremo a extremo debe formalizarse para defensa final.

## 14. Repositorio y Trazabilidad

El proyecto se encuentra disponible en GitHub, lo que facilita versionado, trazabilidad de cambios, continuidad y demostracion tecnica.

- Repositorio remoto detectado: `https://github.com/IngenioSoy26/pin_platform.git`

### Imagen sugerida

- `Figura 14. Repositorio GitHub del proyecto`
- Contenido recomendado: captura de la raiz del repositorio, ramas o historial de commits.
- Ubicacion: en esta misma seccion.

## 15. Conclusiones

PIN Platform constituye una solucion integral que combina Big Data, IoT, GIS y visualizacion aplicada al transporte de carga. Su principal fortaleza es la integracion coherente de datos heterogeneos en una experiencia operativa unica.

El sistema no debe presentarse como totalmente cerrado en todos sus componentes, pero si como una plataforma funcional y seriamente avanzada, con una base tecnica real y un camino claro de cierre. Esa posicion es solida para una defensa academica: demuestra construccion, integracion, visualizacion, analitica y pensamiento arquitectonico.

## 16. Recomendaciones de Presentacion en Word o PDF

Para una entrega final profesional se recomienda este orden:

1. Portada
2. Resumen ejecutivo
3. Introduccion y contexto del reto
4. Objetivos
5. Metodologia por fases
6. Arquitectura del sistema
7. Modelo de datos
8. Fuentes de datos y datasets
9. Implementacion tecnica
10. Resultados
11. Limitaciones
12. GitHub y trazabilidad
13. Conclusiones
14. Bibliografia / fuentes
15. Anexos

## 17. Bibliografia y Fuentes Sugeridas

- Ficha del reto aprobada: `Ficha Reto Aprobada Gustavo Alonzo Segrera Gomez - Big Data.pdf`
- Documento de base de datos: `BASE DE DATOS.docx`
- Diagrama ER: `ER PIN.png`
- Repositorio del proyecto: `https://github.com/IngenioSoy26/pin_platform.git`
- FHWA HPMS: `https://www.fhwa.dot.gov/policyinformation/hpms.cfm`
- BTS Monthly Transportation Statistics: `https://www.bts.gov/monthly-transportation-statistics`
- AFDC Alternative Fueling Station Locator: `https://afdc.energy.gov/stations/`
- OpenStreetMap: `https://www.openstreetmap.org/`
- EPA Infrastructure and Recycling sources: `https://www.epa.gov/`
- BTS GeoData (NTAD): `https://geodata.bts.gov/`
- Truck Stop Parking (NTAD): `https://geodata.bts.gov/datasets/usdot::truck-stop-parking/about`
- National Highway System (NTAD): `https://geodata.bts.gov/datasets/usdot::national-highway-system-nhs/about`
- HPMS (catalog.data.gov): `https://catalog.data.gov/dataset/highway-performance-monitoring-system-hpms`
- Truck Size and Weight Enforcement Data: `https://catalog.data.gov/dataset/truck-size-and-weight-enforcement-data`
- FMCSA Company Census File: `https://data.transportation.gov/Trucking-and-Motorcoaches/Company-Census-File/az4n-8mr2`
- EPA Debris Recovery Map: `https://www.epa.gov/debris-recovery-map`
- NWS API (clima/alertas): `https://www.weather.gov/documentation/services-web-api`

## 18. Anexos Recomendados

- Anexo A. Capturas de dashboards
- Anexo B. Captura del dashboard ETL
- Anexo C. Payload de ejemplo para API IoT
- Anexo D. ERD completo
- Anexo E. Tabla de datasets cargados: `docs/ANEXO_E_TABLA_DATASETS.md`
- Anexo F. Evidencia del repositorio GitHub
