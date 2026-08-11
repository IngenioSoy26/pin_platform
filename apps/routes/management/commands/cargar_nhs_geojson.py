"""
Comando Django: cargar_nhs_geojson

Carga el GeoJSON del National Highway System (NHS) que se entrega con el
repositorio PIN Platform en la carpeta data/.

Uso basico:
    python manage.py cargar_nhs_geojson

Uso con ruta explicita (recomendado en instalaciones nuevas):
    python manage.py cargar_nhs_geojson "C:/ruta/al/archivo/NHS.geojson"

Uso avanzado:
    # Solo crea la tabla staging (no escribe en routes_highwayroute)
    python manage.py cargar_nhs_geojson --staging-only

    # No agrupa por estado + sign1 (sube 1 fila / feature, para auditoria)
    python manage.py cargar_nhs_geojson --no-merge

    # Empieza de cero (trunca tabla destino ANTES de insertar)
    python manage.py cargar_nhs_geojson --reset

    # Limita la carga a N features (prueba rapida en instalacion nueva)
    python manage.py cargar_nhs_geojson --limit 5000

Salida:
  - staging routes_nhs_geojson_staging (1 fila por feature del GeoJSON)
  - tabla destino routes_highwayroute (rutas consolidadas por estado y signo
    vial, con geometria en route_geometry::jsonb FeatureCollection)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from time import perf_counter

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

STATES_BY_FIPS: dict[str, str] = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP",
    "72": "PR", "78": "VI",
}


def _haversine_km(coords: list[list[float]]) -> float:
    R = 6371.0088
    to_rad = math.pi / 180.0
    total = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(coords, coords[1:]):
        try:
            lon1 = float(lon1)
            lat1 = float(lat1)
            lon2 = float(lon2)
            lat2 = float(lat2)
        except (TypeError, ValueError):
            continue
        phi1, phi2 = lat1 * to_rad, lat2 * to_rad
        dphi = (lat2 - lat1) * to_rad
        dlmb = (lon2 - lon1) * to_rad
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
        total += 2 * R * math.asin(math.sqrt(a))
    return total


def _state_from_fips(stfips) -> str:
    code = str(stfips or "").strip().zfill(2)
    return STATES_BY_FIPS.get(code, "") or ""


def _map_type(signt1: str, sign1: str, fclass) -> str:
    s = (signt1 or "").strip().upper()
    sign1_str = (sign1 or "").strip().upper()
    if s == "I" or sign1_str.startswith("I-"):
        return "Interstate"
    if s == "U" or sign1_str.startswith("US "):
        return "US Route"
    if s in ("S", "ST", "SR", "SH"):
        return "State Route"
    if s == "C":
        return "County Road"
    try:
        fc = int(fclass)
    except (TypeError, ValueError):
        fc = None
    if fc in (1, 2):
        return "Principal Arterial"
    if fc in (3, 4):
        return "Minor Arterial"
    return "NHS Route"


def _safe_text(v, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _to_int(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _default_geojson_path() -> Path:
    here = Path(__file__).resolve()
    data_dir = here.parents[4] / "data"
    if not data_dir.exists():
        raise CommandError(
            "No se pudo localizar la carpeta data/. "
            "Pasa la ruta absoluta al archivo GeoJSON como primer argumento."
        )
    candidates = sorted(data_dir.glob("NTAD_National_Highway_System*.geojson"))
    if not candidates:
        raise CommandError(
            "No se encontro el archivo NTAD_National_Highway_System*.geojson "
            "dentro de data/. Colocalo alli o indica la ruta completa."
        )
    return candidates[0]


class Command(BaseCommand):
    help = "Carga el GeoJSON NHS en las tablas routes_nhs_geojson_staging y routes_highwayroute."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            type=str,
            default=None,
            help="Ruta al archivo .geojson del NHS. Si se omite, se busca en data/.",
        )
        parser.add_argument(
            "--staging-only",
            action="store_true",
            help="Solo escribe en la tabla staging; no toca routes_highwayroute.",
        )
        parser.add_argument(
            "--no-merge",
            action="store_true",
            help="Sube 1 fila por feature a routes_highwayroute (sin agrupar por estado/signo).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Trunca routes_highwayroute antes de escribir (reinicio total).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limita la carga a las primeras N features del GeoJSON (para pruebas).",
        )
        parser.add_argument(
            "--batch",
            type=int,
            default=10000,
            help="Tamano de lote para COPY a staging. Default 10000.",
        )

    def handle(self, *args, **options):
        t0 = perf_counter()

        # 1) Resolver ruta
        if options.get("path"):
            gj_path = Path(options["path"])
        else:
            gj_path = _default_geojson_path()
        if not gj_path.exists():
            raise CommandError(f"No existe el archivo: {gj_path}")
        self.stdout.write(self.style.SUCCESS(f"[1/6] GeoJSON localizado: {gj_path}"))

        # 2) Leer features
        self.stdout.write("[2/6] Leyendo GeoJSON (esto puede tardar algunos segundos)...")
        with open(gj_path, "r", encoding="utf-8") as f:
            gj = json.load(f)
        features = gj.get("features") or []
        limit = options.get("limit")
        if limit and limit > 0:
            features = features[:limit]
        n = len(features)
        if n == 0:
            raise CommandError("El GeoJSON no contiene features.")
        self.stdout.write(self.style.SUCCESS(f"       -> {n} features detectadas."))

        # 3) Crear staging
        self.stdout.write("[3/6] Creando tabla staging (routes_nhs_geojson_staging).")
        batch_size = max(int(options.get("batch") or 10000), 1)
        self._create_staging(reset=True)

        # 4) Cargar staging con COPY
        self.stdout.write("[4/6] Insertando staging via COPY (por lotes).")
        n_staging = self._copy_staging(features, batch_size)
        self.stdout.write(self.style.SUCCESS(f"       -> {n_staging} filas insertadas en staging."))

        # 5) Normalizacion a routes_highwayroute (si procede)
        if options.get("staging_only"):
            self.stdout.write(self.style.WARNING("[5/6] Omitida normalizacion: modo --staging-only."))
        else:
            reset = bool(options.get("reset"))
            merge = not bool(options.get("no_merge"))
            self.stdout.write(
                f"[5/6] Normalizando a routes_highwayroute (merge={merge}, reset={reset})."
            )
            n_dest, by_state_10 = self._normalize_to_highwayroute(reset=reset, merge=merge)
            self.stdout.write(self.style.SUCCESS(f"       -> {n_dest} filas en routes_highwayroute."))
            if by_state_10:
                self.stdout.write("       Top 10 estados por cantidad de rutas:")
                for row in by_state_10:
                    self.stdout.write(
                        f"         - {row[0]!s:<5}  n={row[1]:<6}  km={row[2]}"
                    )

        # 6) Resumen final
        dt = perf_counter() - t0
        self.stdout.write(self.style.SUCCESS(f"[6/6] Terminado en {dt:.1f} segundos."))
        self.stdout.write("Tareas de verificacion rapida (si quieres validar manualmente):")
        self.stdout.write("  SELECT COUNT(*) FROM routes_nhs_geojson_staging;")
        self.stdout.write("  SELECT COUNT(*) FROM routes_highwayroute;")

    # ------------------------------------------------------------------ helpers
    def _create_staging(self, *, reset: bool):
        with connection.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS routes_nhs_geojson_staging (
                    id              bigserial PRIMARY KEY,
                    feature_id      bigint,
                    objectid        bigint,
                    fips_code       text,
                    state_abbrev    text,
                    route_id_src    text,
                    sign1           text,
                    signt1          text,
                    signn1          text,
                    lname           text,
                    miles           numeric,
                    nhs_code        integer,
                    fclass          integer,
                    aadt            integer,
                    aadt_com        integer,
                    aadt_single     integer,
                    speed_limi      integer,
                    year_recorded   integer,
                    file_name       text,
                    geometry_json   jsonb NOT NULL,
                    properties_json jsonb NOT NULL,
                    loaded_at       timestamptz NOT NULL DEFAULT clock_timestamp(),
                    length_km       numeric
                );
                """
            )
            if reset:
                cur.execute("TRUNCATE TABLE routes_nhs_geojson_staging RESTART IDENTITY;")
            try:
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_routes_nhs_staging_state_sign "
                    "ON routes_nhs_geojson_staging(state_abbrev, sign1, route_id_src);"
                )
            except Exception:
                pass

    def _iter_rows(self, features: list[dict]):
        for ft in features:
            geom = ft.get("geometry") or {}
            geom_type = geom.get("type")
            p = ft.get("properties") or {}
            coords = geom.get("coordinates") or []
            if geom_type == "LineString":
                flat = coords
            elif geom_type == "MultiLineString":
                flat = [pt for ls in coords for pt in ls]
            else:
                flat = []
            st = _state_from_fips(p.get("STFIPS"))
            length_km = _haversine_km(flat)
            yield (
                _to_int(ft.get("id")),
                _to_int(p.get("OBJECTID")),
                str(p.get("STFIPS") or "").strip().zfill(2),
                st,
                _safe_text(p.get("ROUTEID")),
                _safe_text(p.get("SIGN1")),
                _safe_text(p.get("SIGNT1")),
                _safe_text(p.get("SIGNN1")),
                _safe_text(p.get("LNAME")),
                _to_float(p.get("MILES")),
                _to_int(p.get("NHS")),
                _to_int(p.get("FCLASS")),
                _to_int(p.get("AADT")),
                _to_int(p.get("AADT_COM")),
                _to_int(p.get("AADT_SINGL")),
                _to_int(p.get("SPEED_LIMI")),
                _to_int(p.get("YEAR")),
                _safe_text(p.get("FILE_NAME")),
                json.dumps(geom, ensure_ascii=False),
                json.dumps(p, ensure_ascii=False),
                round(length_km, 6),
            )

    def _copy_staging(self, features: list[dict], batch_size: int) -> int:
        total = 0
        columns = [
            "feature_id", "objectid", "fips_code", "state_abbrev", "route_id_src",
            "sign1", "signt1", "signn1", "lname", "miles", "nhs_code", "fclass",
            "aadt", "aadt_com", "aadt_single", "speed_limi", "year_recorded",
            "file_name", "geometry_json", "properties_json", "length_km",
        ]
        sql = (
            "COPY routes_nhs_geojson_staging ("
            + ",".join(columns)
            + ") FROM STDIN"
        )

        def chunked(seq, size):
            buf = []
            for x in seq:
                buf.append(x)
                if len(buf) >= size:
                    yield buf
                    buf = []
            if buf:
                yield buf

        with transaction.atomic():
            with connection.cursor() as cur:
                for batch in chunked(self._iter_rows(features), batch_size):
                    with cur.copy(sql) as copy:
                        for row in batch:
                            copy.write_row(row)
                    total += len(batch)
                    if total % (batch_size * 5) == 0:
                        self.stdout.write(f"         staging ... {total}")

        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM routes_nhs_geojson_staging;")
            return cur.fetchone()[0]

    def _normalize_to_highwayroute(self, *, reset: bool, merge: bool):
        with connection.cursor() as cur:
            # Asegurarse que exista la tabla destino (por si acaso alguien corre
            # este comando antes que migrate). Si no existe, fallamos con claro.
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public' AND table_name='routes_highwayroute'
                );
                """
            )
            if not cur.fetchone()[0]:
                raise CommandError(
                    "No existe la tabla routes_highwayroute. "
                    "Ejecuta primero: python manage.py migrate"
                )

            if reset:
                cur.execute("TRUNCATE TABLE routes_highwayroute RESTART IDENTITY CASCADE;")

            if merge:
                cur.execute(self._sql_merge_by_state_sign())
            else:
                cur.execute(self._sql_one_row_per_feature())

            cur.execute("SELECT COUNT(*) FROM routes_highwayroute;")
            n_dest = cur.fetchone()[0]

            cur.execute(
                """
                SELECT state, COUNT(*), ROUND(SUM(length_km)::numeric, 0) AS km_total
                FROM routes_highwayroute
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT 10;
                """
            )
            top10 = list(cur.fetchall())
        return n_dest, top10

    @staticmethod
    def _sql_merge_by_state_sign() -> str:
        return """
            WITH agg AS (
                SELECT
                    state_abbrev                                   AS state,
                    COALESCE(NULLIF(TRIM(sign1),''), route_id_src) AS sign_key,
                    MAX(
                        state_abbrev || '-' ||
                        COALESCE(NULLIF(TRIM(sign1),''), route_id_src)
                    )                                              AS route_id,
                    MAX(
                        COALESCE(NULLIF(TRIM(lname),''),
                                 NULLIF(TRIM(sign1),''),
                                 route_id_src,
                                 'Unnamed NHS Route')
                    )                                              AS route_name,
                    MAX(
                        CASE
                          WHEN TRIM(signt1) = 'I' THEN 'Interstate'
                          WHEN TRIM(signt1) = 'U' THEN 'US Route'
                          WHEN TRIM(signt1) IN ('S','ST','SR','SH') THEN 'State Route'
                          WHEN TRIM(signt1) = 'C' THEN 'County Road'
                          WHEN fclass IN (1,2) THEN 'Principal Arterial'
                          WHEN fclass IN (3,4) THEN 'Minor Arterial'
                          ELSE 'NHS Route'
                        END
                    )                                              AS route_type,
                    ROUND(
                      SUM(COALESCE(length_km, miles * 1.609344, 0))::numeric, 4
                    )::float8                                       AS length_km,
                    TRUE                                           AS is_active,
                    jsonb_build_object(
                      'type', 'FeatureCollection',
                      'features',
                      jsonb_agg(
                        jsonb_build_object(
                          'type', 'Feature',
                          'id', objectid,
                          'properties',
                            jsonb_build_object(
                              'objectid',      objectid,
                              'route_id_src',  route_id_src,
                              'sign1',         sign1,
                              'signt1',        signt1,
                              'signn1',        signn1,
                              'lname',         lname,
                              'fclass',        fclass,
                              'aadt',          aadt,
                              'aadt_com',      aadt_com,
                              'aadt_single',   aadt_single,
                              'speed_limi',    speed_limi,
                              'year_recorded', year_recorded,
                              'file_name',     file_name,
                              'miles',         miles,
                              'nhs_code',      nhs_code
                            ),
                          'geometry', geometry_json
                        )
                      )
                    )                                              AS route_geometry
                FROM routes_nhs_geojson_staging
                WHERE state_abbrev <> ''
                  AND (NULLIF(TRIM(sign1),'') IS NOT NULL OR route_id_src <> '')
                GROUP BY state_abbrev,
                         COALESCE(NULLIF(TRIM(sign1),''), route_id_src)
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
        """

    @staticmethod
    def _sql_one_row_per_feature() -> str:
        return """
            WITH src AS (
                SELECT
                    CASE
                      WHEN state_abbrev <> '' AND sign1 <> ''
                        THEN state_abbrev || '-' || sign1 || '__' || COALESCE(objectid, id)::text
                      WHEN state_abbrev <> ''
                        THEN state_abbrev || '-' || COALESCE(NULLIF(route_id_src,''), 'NHS') || '__' || COALESCE(objectid, id)::text
                      ELSE 'NHS__' || COALESCE(objectid, id)::text
                    END                                                AS route_id,
                    COALESCE(NULLIF(TRIM(lname),''),
                             NULLIF(TRIM(sign1),''),
                             route_id_src,
                             'Unnamed NHS Route')                         AS route_name,
                    CASE
                      WHEN TRIM(signt1) = 'I' THEN 'Interstate'
                      WHEN TRIM(signt1) = 'U' THEN 'US Route'
                      WHEN TRIM(signt1) IN ('S','ST','SR','SH') THEN 'State Route'
                      WHEN TRIM(signt1) = 'C' THEN 'County Road'
                      WHEN fclass IN (1,2) THEN 'Principal Arterial'
                      WHEN fclass IN (3,4) THEN 'Minor Arterial'
                      ELSE 'NHS Route'
                    END                                                AS route_type,
                    state_abbrev                                       AS state,
                    ROUND(COALESCE(length_km, miles * 1.609344, 0)::numeric, 4)::float8 AS length_km,
                    TRUE                                               AS is_active,
                    jsonb_build_object(
                      'type','FeatureCollection',
                      'features', jsonb_build_array(
                        jsonb_build_object(
                          'type','Feature',
                          'id', objectid,
                          'properties', properties_json,
                          'geometry', geometry_json
                        )
                      )
                    )                                                  AS route_geometry
                FROM routes_nhs_geojson_staging
            )
            INSERT INTO routes_highwayroute
                (route_id, route_name, route_type, state, length_km, is_active, route_geometry)
            SELECT route_id, route_name, route_type, state, length_km, is_active, route_geometry
            FROM src
            ON CONFLICT (route_id) DO UPDATE SET
                route_name     = EXCLUDED.route_name,
                route_type     = EXCLUDED.route_type,
                state          = EXCLUDED.state,
                length_km      = EXCLUDED.length_km,
                is_active      = EXCLUDED.is_active,
                route_geometry = EXCLUDED.route_geometry;
        """
