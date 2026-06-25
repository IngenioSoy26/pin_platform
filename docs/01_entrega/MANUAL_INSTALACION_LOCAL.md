# Manual de instalación local (paso a paso)

Este manual describe cómo levantar PIN Platform en local desde cero, partiendo desde la clonación del repositorio. Incluye dos modos:

- **Modo mínimo (recomendado para arrancar rápido):** SQLite + dependencias básicas.
- **Modo completo (recomendado para geoespacial/analítica):** PostGIS + dependencias full (geopandas/leaflet/ML).

## 1) Prerrequisitos

En Windows:

- Git instalado y disponible en terminal (`git --version`).
- Python `3.11` o `3.12` (`python --version`).
- (Opcional) PostgreSQL + PostGIS si usarás geoespacial completo.

## 2) Clonar el repositorio

En PowerShell (elige una carpeta de trabajo):

```bash
git clone https://github.com/IngenioSoy26/pin_platform.git
cd pin_platform
```

Verifica que estás en la rama principal:

```bash
git branch
```

## 3) Crear y activar el entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

## 4) Instalar dependencias

### Opción A: instalación mínima (arranque rápido)

```bash
python -m pip install -r requirements.txt
```

### Opción B: instalación completa (geoespacial + analítica)

```bash
python -m pip install -r requirements-full.txt
```

Nota: si vas a usar **ENABLE_GIS=True** (PostGIS/GIS), usa la opción B porque incluye `django-leaflet` y librerías geoespaciales.

## 5) Configurar variables de entorno (.env)

El proyecto lee variables desde un archivo `.env` en la raíz del repositorio (misma carpeta que `manage.py`). Si no existe, funciona con valores por defecto (SQLite).

### Configuración mínima (SQLite)

No es obligatorio crear `.env`. Si quieres explicitarlo:

```env
DB_ENGINE=sqlite
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SECRET_KEY=dev-secret-key
```

### Configuración recomendada (PostgreSQL/PostGIS)

Si tienes PostGIS y quieres funciones geoespaciales completas:

```env
DB_ENGINE=postgis
ENABLE_GIS=True
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SECRET_KEY=dev-secret-key

DB_NAME=truck_routes_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

Nota Windows: si PostgreSQL fue instalado localmente, PIN intenta detectar automaticamente su carpeta `bin` para encontrar `libpq.dll` (por ejemplo `C:\Postgres\bin` o `C:\Program Files\PostgreSQL\<version>\bin`). Si tu instalacion usa otra ruta, puedes definirla con la variable de entorno `POSTGRES_BIN`.

## 6) Inicializar la base de datos

Ejecuta:

```bash
python manage.py check
python manage.py migrate
```

Opcional (para entrar al admin):

```bash
python manage.py createsuperuser
```

## 7) Preparar datasets locales

El repositorio puede incluir una parte de los datasets operativos en `data/`. Los archivos de gran tamano pueden gestionarse aparte o mediante Git LFS, segun el estado del repositorio remoto.

Rutas por defecto (pueden ajustarse con `DATA_DIR` y `DATASET_DIR` en `.env`):

- `data/` → datasets operativos (CSV/Excel/GeoJSON) usados por el ETL.
- `dataset/` → (si aplica) otros insumos grandes auxiliares.

Fuentes/URLs oficiales: ver [FUENTES_DATASETS.md](FUENTES_DATASETS.md).

## 8) Ejecutar carga ETL de datasets (si ya descargaste archivos)

Coloca tus archivos en `data/` (por ejemplo: CSV/XLSX/GEOJSON) y ejecuta:

```bash
python manage.py cargar_datos_csv
```

Si tus datasets están en otra carpeta:

```bash
python manage.py cargar_datos_csv --dir "C:\ruta\absoluta\a\mis_datasets"
```

El comando:

- crea/actualiza registros `DataSource` por archivo,
- crea un `ETLJob` por archivo,
- ejecuta el motor ETL y deja logs por dataset.

## 9) (Opcional) Sincronizar inventario HPMS y enriquecer rugosidad

Si descargaste el CSV maestro de HPMS a `data/Highway_Performance_Monitoring_System__HPMS_.csv`, puedes sincronizar:

```bash
python manage.py sync_hpms
```

Opcionalmente, intentar descubrimiento de servicios remotos y matching con rutas:

```bash
python manage.py sync_hpms --discover --limit 5
python manage.py sync_hpms --match
```

## 10) Levantar el servidor web

```bash
python manage.py runserver
```

Abre en el navegador:

- `http://localhost:8000/`
- `http://localhost:8000/map/`
- `http://localhost:8000/dashboards/resumen/`
- `http://localhost:8000/dashboards/iot/`
- `http://localhost:8000/dashboards/geoespacial/`
- `http://localhost:8000/admin/` (si creaste superusuario)

## 11) Problemas frecuentes (rápido)

- **Error de GIS/leaflet:** si activaste `ENABLE_GIS=True`, instala dependencias full (`requirements-full.txt`) y reintenta.
- **ETL no encuentra archivos:** verifica que exista `data/` y que los archivos tengan extensión `.csv`, `.xlsx`, `.xls` o `.geojson`.
- **Dashboards sin datos:** ejecuta ETL y/o ingesta IoT; algunas gráficas dependen de registros en base de datos.
