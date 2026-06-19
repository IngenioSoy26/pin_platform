# PIN Platform

Plataforma web IoT + Big Data para monitoreo de tractomulas, llantas, cumplimiento HOS, peso vehicular, rutas y servicios de apoyo en EE.UU.

## Estado actual

Este repositorio queda preparado con la Fase 1 del sistema final:
- estructura completa de carpetas
- configuracion base de Django
- soporte para cambiar entre SQLite y PostGIS
- configuracion minima de ASGI, WSGI y Celery
- interfaz base con logo institucional
- instalacion inicial simplificada para Windows

## Alcance del sistema final

La meta final del proyecto incluye:
- ETL para 16 datasets en `dataset/`
- monitoreo IoT de 18 llantas por tractomula
- reglas HOS FMCSA
- monitoreo de peso y regulaciones federales
- motor de alertas y recomendaciones
- dashboards y API REST
- modelos predictivos y simulador IoT

## Requisitos sugeridos

- Python 3.11 o superior
- pip actualizado
- PostgreSQL + PostGIS para fases posteriores
- Redis para Channels y Celery en fases posteriores

## Importante sobre el entorno

- Si activas `.venv`, usa `python` y `python -m pip`, no `py`.
- En tu equipo, `py` apunta a Python `3.14`, y varias librerias cientificas del sistema final no estan listas para esa ruta en Windows.
- Para la Fase 1 usa `requirements.txt`.
- Para las fases con ETL, GIS y ML usa `requirements-full.txt`, idealmente con Python `3.12`.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

## Stack completo mas adelante

```bash
python -m pip install -r requirements-full.txt
```

## Configuracion de base de datos

En Fase 1 el archivo `.env` deja `DB_ENGINE=sqlite` para que el arranque inicial sea sencillo.
Cuando empecemos la capa geoespacial y los modelos con `PointField`, cambia a:

```env
DB_ENGINE=postgis
ENABLE_GIS=True
DB_NAME=truck_routes_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

## Dataset disponibles

Los 16 archivos fuente se encuentran en `dataset/` y se incorporaran en la fase de ingesta.

## Siguientes fases

1. Modelos base y utilidades compartidas
2. Ingesta y normalizacion de datasets
3. Modelado IoT, HOS y peso
4. API, dashboards, analitica y simulacion
