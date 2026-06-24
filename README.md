# PIN Platform

Plataforma web IoT + Big Data para monitoreo de tractomulas, llantas, cumplimiento HOS, peso vehicular, rutas, amenidades operativas y analitica aplicada al transporte de carga en EE.UU.

## Resumen

PIN Platform integra cuatro dominios principales:

- telemetria IoT para tractomulas y sensores de llantas;
- cumplimiento normativo HOS, peso y seguridad operacional;
- capa geoespacial para rutas, rugosidad, clima, cierres y servicios;
- analitica descriptiva y predictiva para soporte a decisiones.

El proyecto ya cuenta con una base funcional amplia: ETL con seguimiento de progreso, dashboards web, mapas live, capas geoespaciales tematicas, API de ingesta IoT y modelos analiticos base. Aun requiere cierre documental y validacion formal de algunos componentes para considerarse entregable final.

## Estado actual del repositorio

Estado estimado respecto al plan maestro:

- `Fases 1-8`: implementadas en buena parte y operativas.
- `Fase 9`: implementada a nivel estructural, pendiente de validacion formal de entrenamiento y metricas.
- `Fase 10`: parcialmente implementada con demo/live sync y logica sintetica; requiere cierre formal del simulador extremo a extremo.
- `Fases 11-12`: muy avanzadas y activamente usadas.
- `Fase 13`: parcial, con APIs utiles pero sin cierre documental unificado.
- `Fases 14-15`: incompletas como paquete final de entrega.

## Documentacion principal

La documentacion entregable del proyecto se encuentra en `docs/`:

- `MANUAL_INSTALACION_LOCAL.md` (instalacion local paso a paso)
- `MEMORIA_FINAL_PRESENTACION.md` (documento principal)
- `INFORME_BASE_DATOS.md` (soporte del modelo de datos)
- `FUENTES_DATASETS.md` (portales y citacion)
- `ANEXO_E_TABLA_DATASETS.md` (tabla consolidada por archivo)

## Requisitos recomendados

- Python `3.11` o `3.12`
- `pip` actualizado
- SQLite para arranque rapido
- PostgreSQL + PostGIS para despliegue geoespacial completo
- Redis/Celery/Channels si se desea evolucionar a tiempo real distribuido

## Puesta en marcha rapida

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

## Configuracion de base de datos

Configuracion minima:

```env
DB_ENGINE=sqlite
```

Configuracion recomendada para geoespacial:

```env
DB_ENGINE=postgis
ENABLE_GIS=True
DB_NAME=truck_routes_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

## Endpoints y vistas relevantes

- `http://localhost:8000/dashboard/`
- `http://localhost:8000/map/`
- `http://localhost:8000/dashboards/resumen/`
- `http://localhost:8000/dashboards/iot/`
- `http://localhost:8000/dashboards/geoespacial/`
- `http://localhost:8000/configuracion/`
- `http://localhost:8000/api/iot/reading/`
- `http://localhost:8000/routes/hpms/roughness-geojson/`

## Pendientes para cierre entregable

- consolidar documentacion final y checklist de aceptacion;
- validar entrenamiento real de modelos ML;
- cerrar estrategia de simulacion end-to-end;
- fortalecer APIs unificadas y documentacion OpenAPI;
- completar migracion geoespacial real a PostGIS donde aplique.
