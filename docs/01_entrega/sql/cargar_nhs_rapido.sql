-- =========================================================================
-- Script auxiliar: Carga rapida del GeoJSON NHS en PostgreSQL
-- Proyecto: PIN Platform
-- Uso:    psql -h localhost -U postgres -d <BASE> -f cargar_nhs_rapido.sql
--         o ejecuta el bloque en pgAdmin / DBeaver
--
-- Requisito previo EN EL CLIENTE (solo una vez):
--   1. Generar un CSV plano con TODAS las features del GeoJSON (1 fila/feature)
--      Ese CSV se genera con 1 linea de PowerShell (ver abajo).
--   2. El comando COPY del servidor requiere acceso a la ruta, asi que este
--      script usa \copy (CLIENT SIDE COPY) si ejecutas con psql; en pgAdmin
--      usa la funcion PL/pgSQL + pg_read_binary_file alternativa.
--
-- NOTA:
--   Si no quieres pegar SQL, usa el comando Django oficial que funciona
--   en SQLite Y PostgreSQL SIN PostGIS y sin dependencias extra:
--         python manage.py cargar_nhs_geojson
-- =========================================================================

-- -------------------------------------------------------------------------
-- 0. CONFIGURACION RAPIDA (ajusta aqui el nombre de tu base y de la ruta)
--    En el manual "truck_routes_db" es el nombre por defecto de ejemplo.
--    En tu entorno local puedes usar "pin_database". Este script no depende
--    del nombre, asi que funciona para ambos.
-- -------------------------------------------------------------------------
-- Base de datos a usar (ejecuta este comentado y ya):
-- \connect pin_database;
-- \connect truck_routes_db;

-- -------------------------------------------------------------------------
-- A. PASO 1: GENERAR CSV PLANO A PARTIR DEL GEOJSON
--    (HAZLO EN POWERSHELL, no en SQL)
-- -------------------------------------------------------------------------
-- cd "C:\ruta\a\pin_platform"
-- .\.venv\Scripts\python.exe -c "
-- import json, csv, sys
-- from pathlib import Path
-- gj_path = Path('data/NTAD_National_Highway_System_-2908344783259962276.geojson')
-- out     = Path('_staging_nhs_features.csv')
-- with gj_path.open('r', encoding='utf-8') as fp:
--     gj = json.load(fp)
-- with out.open('w', encoding='utf-8', newline='') as fp:
--     w = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
--     w.writerow(['feature_json'])
--     for ft in gj.get('features', []):
--         w.writerow([json.dumps(ft, ensure_ascii=False)])
-- print(out.resolve())
-- "
-- Salida:
--   C:\ruta\a\pin_platform\_staging_nhs_features.csv

-- -------------------------------------------------------------------------
-- B. PASO 2: TABLA STAGING CRUDA
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS routes_nhs_geojson_staging (
    id              bigserial PRIMARY KEY,
    feature_json    jsonb NOT NULL,
    loaded_at       timestamptz NOT NULL DEFAULT clock_timestamp()
);
TRUNCATE TABLE routes_nhs_geojson_staging RESTART IDENTITY;

-- -------------------------------------------------------------------------
-- C. PASO 3: CLIENT-SIDE COPY DESDE EL CSV GENERADO
--    (usa \copy solo si estas dentro de psql; si usas pgAdmin/DBeaver usa
--     el importador CSV nativo de la herramienta y apunta a esta tabla)
-- -------------------------------------------------------------------------
-- \copy routes_nhs_geojson_staging(feature_json) \
--   FROM 'C:/ruta/a/pin_platform/_staging_nhs_features.csv' \
--   WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', QUOTE '"');

-- -------------------------------------------------------------------------
-- D. PASO 4: VISTA NORMALIZADA (solo para inspeccion visual)
-- -------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_nhs_staging_extracted AS
SELECT
    id,
    (feature_json->>'id')::bigint                                 AS feature_id,
    (feature_json#>>'{properties,OBJECTID}')::bigint              AS objectid,
    LPAD(COALESCE(feature_json#>>'{properties,STFIPS}',''),2,'0') AS fips_code,
    feature_json#>>'{properties,ROUTEID}'                         AS route_id_src,
    feature_json#>>'{properties,SIGN1}'                           AS sign1,
    feature_json#>>'{properties,SIGNT1}'                          AS signt1,
    feature_json#>>'{properties,SIGNN1}'                          AS signn1,
    feature_json#>>'{properties,LNAME}'                           AS lname,
    NULLIF((feature_json#>>'{properties,MILES}')::numeric,0)      AS miles,
    (feature_json#>>'{properties,FCLASS}')::integer               AS fclass,
    (feature_json#>>'{properties,AADT}')::integer                 AS aadt,
    (feature_json#>>'{properties,YEAR}')::integer                 AS year_recorded,
    feature_json#>>'{properties,FILE_NAME}'                       AS file_name,
    feature_json#>'{geometry}'                                    AS geometry_json,
    feature_json#>'{properties}'                                  AS properties_json
FROM routes_nhs_geojson_staging;

-- -------------------------------------------------------------------------
-- E. PASO 5: UPSERT CONSOLIDADO A routes_highwayroute
--    (merge por STATE + SIGN1, igual que el comando Django oficial)
-- -------------------------------------------------------------------------
WITH fips AS (
    SELECT '01' f,'AL' s UNION SELECT '02','AK' UNION SELECT '04','AZ'
    UNION SELECT '05','AR' UNION SELECT '06','CA' UNION SELECT '08','CO'
    UNION SELECT '09','CT' UNION SELECT '10','DE' UNION SELECT '11','DC'
    UNION SELECT '12','FL' UNION SELECT '13','GA' UNION SELECT '15','HI'
    UNION SELECT '16','ID' UNION SELECT '17','IL' UNION SELECT '18','IN'
    UNION SELECT '19','IA' UNION SELECT '20','KS' UNION SELECT '21','KY'
    UNION SELECT '22','LA' UNION SELECT '23','ME' UNION SELECT '24','MD'
    UNION SELECT '25','MA' UNION SELECT '26','MI' UNION SELECT '27','MN'
    UNION SELECT '28','MS' UNION SELECT '29','MO' UNION SELECT '30','MT'
    UNION SELECT '31','NE' UNION SELECT '32','NV' UNION SELECT '33','NH'
    UNION SELECT '34','NJ' UNION SELECT '35','NM' UNION SELECT '36','NY'
    UNION SELECT '37','NC' UNION SELECT '38','ND' UNION SELECT '39','OH'
    UNION SELECT '40','OK' UNION SELECT '41','OR' UNION SELECT '42','PA'
    UNION SELECT '44','RI' UNION SELECT '45','SC' UNION SELECT '46','SD'
    UNION SELECT '47','TN' UNION SELECT '48','TX' UNION SELECT '49','UT'
    UNION SELECT '50','VT' UNION SELECT '51','VA' UNION SELECT '53','WA'
    UNION SELECT '54','WV' UNION SELECT '55','WI' UNION SELECT '56','WY'
    UNION SELECT '72','PR'
),
mapped AS (
    SELECT
        COALESCE(f.s, '')                                          AS state,
        COALESCE(NULLIF(TRIM(v.sign1),''), v.route_id_src)         AS sign_key,
        v.sign1,
        v.route_id_src,
        v.signt1,
        v.lname,
        v.fclass,
        v.miles,
        v.geometry_json,
        v.objectid,
        v.properties_json
    FROM vw_nhs_staging_extracted v
    LEFT JOIN fips f ON f.f = v.fips_code
),
agg AS (
    SELECT
        state,
        sign_key,
        MAX(state || '-' || sign_key)                                AS route_id,
        MAX(
            COALESCE(NULLIF(TRIM(lname),''),
                     NULLIF(TRIM(sign1),''),
                     route_id_src,
                     'Unnamed NHS Route')
        )                                                            AS route_name,
        MAX(CASE
              WHEN TRIM(signt1) = 'I' THEN 'Interstate'
              WHEN TRIM(signt1) = 'U' THEN 'US Route'
              WHEN TRIM(signt1) IN ('S','ST','SR','SH') THEN 'State Route'
              WHEN TRIM(signt1) = 'C' THEN 'County Road'
              WHEN fclass IN (1,2)   THEN 'Principal Arterial'
              WHEN fclass IN (3,4)   THEN 'Minor Arterial'
              ELSE 'NHS Route'
            END)                                                     AS route_type,
        ROUND(SUM(COALESCE(miles,0) * 1.609344)::numeric, 4)::float8 AS length_km,
        TRUE                                                         AS is_active,
        jsonb_build_object(
            'type','FeatureCollection',
            'features',
            jsonb_agg(
                jsonb_build_object(
                    'type','Feature',
                    'id', objectid,
                    'properties', properties_json,
                    'geometry', geometry_json
                )
            )
        )                                                            AS route_geometry
    FROM mapped
    WHERE state <> ''
      AND sign_key <> ''
    GROUP BY state, sign_key
)
INSERT INTO routes_highwayroute
    (route_id, route_name, route_type, state, length_km, is_active, route_geometry)
SELECT
    route_id,
    route_name,
    route_type,
    state,
    length_km,
    is_active,
    route_geometry
FROM agg
ON CONFLICT (route_id) DO UPDATE SET
    route_name     = EXCLUDED.route_name,
    route_type     = EXCLUDED.route_type,
    state          = EXCLUDED.state,
    length_km      = EXCLUDED.length_km,
    is_active      = EXCLUDED.is_active,
    route_geometry = EXCLUDED.route_geometry;

-- -------------------------------------------------------------------------
-- F. PASO 6: VERIFICACION RAPIDA (una vez terminado)
-- -------------------------------------------------------------------------
SELECT 'staging'     AS origen, COUNT(*) AS n FROM routes_nhs_geojson_staging
UNION ALL
SELECT 'destination', COUNT(*) FROM routes_highwayroute;

SELECT state, COUNT(*) AS n_rutas,
       ROUND(SUM(length_km)::numeric, 0) AS km_total
FROM routes_highwayroute
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15;
