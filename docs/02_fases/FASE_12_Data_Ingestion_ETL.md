# Fase 12: Data Ingestion y ETL

## Resumen
Esta fase formalizó la carga y trazabilidad de datasets estáticos y geoespaciales dentro de PIN Platform. Su propósito fue convertir archivos heterogéneos en datos estructurados utilizables por mapas, dashboards y procesos analíticos.

## Objetivo de la fase
- Diseñar el flujo ETL del proyecto.
- Registrar datasets y ejecuciones.
- Cargar información desde CSV, Excel y GeoJSON.
- Dejar una base reproducible para poblar el sistema localmente.

## Componentes implementados

### 1. Modelos de control ETL
En `apps/data_ingestion/models.py` se implementaron:

- `DataSource`: catálogo de fuentes cargadas.
- `ETLJob`: seguimiento del estado de las ejecuciones.

Estos modelos permiten trazabilidad de carga, fecha de última ejecución y volumen procesado.

### 2. Motor ETL
En `apps/data_ingestion/etl.py` se centralizó la lógica de parsing, limpieza y procesamiento para múltiples datasets del proyecto.

### 3. Comando de gestión
Se implementó el comando:

```bash
python manage.py cargar_datos_csv
```

Este comando permite poblar el sistema con los datasets locales ubicados en `data/`.

### 4. Interfaz de configuración y monitoreo
La app `data_ingestion` también aporta la capa de configuración y la visualización de progreso ETL desde la interfaz web del proyecto.

## Tipos de datos integrados
- rutas y corredores
- truck stops y amenidades
- estaciones de combustible alternativo
- talleres y servicios asociados a llantas
- WIM y enforcement
- carriers y estadísticas sectoriales
- fuentes HPMS y soporte para rugosidad vial

## Flujo general de la fase
1. Identificación del archivo fuente.
2. Validación de formato y estructura.
3. Limpieza y normalización.
4. Transformación a estructuras del dominio PIN.
5. Registro de la carga en `DataSource` y `ETLJob`.

## Resultado de la fase
La plataforma quedó con un pipeline ETL funcional para inicializar el sistema a partir de datos locales, evitando depender exclusivamente de carga manual o inserciones directas sobre la base.

## Relación con otras fases
- Alimenta los dashboards de la Fase 11.
- Soporta la capa geoespacial y la rugosidad vial.
- Provee contexto a recomendaciones, cumplimiento y analítica predictiva.

## Estado real de cumplimiento
- La fase está implementada de manera funcional.
- El alcance real dependió de la disponibilidad local de datasets en `data/`.
- Para la entrega final se decidió no subir esos datasets a GitHub por tamaño, dejando documentada su descarga y carga local.
