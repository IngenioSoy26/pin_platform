# Manual de instalacion local desde cero

Esta guia esta pensada para que cualquier persona pueda instalar una copia limpia de PIN Platform en Windows 10 u 11, aunque no conozca el proyecto.

La guia incluye dos recorridos:

- **Ruta recomendada para una instalacion exitosa a la primera:** Python + SQLite.
- **Ruta completa y opcional:** Python + PostgreSQL/PostGIS.

Si lo que buscas es comprobar que el proyecto abre, ejecuta y responde correctamente, empieza por la ruta con SQLite. Es la mas simple y la mas estable para una primera instalacion.

## 1. Objetivo de esta guia

Al terminar, deberias poder:

1. descargar una copia limpia del repositorio;
2. crear un entorno virtual nuevo;
3. instalar las dependencias correctas;
4. inicializar la base de datos;
5. arrancar el servidor en local;
6. abrir la aplicacion en el navegador sin depender de archivos previos.

## 2. Antes de empezar

### 2.1. Que necesitas instalado

En un equipo Windows debes tener:

- Git
- Python **3.11** o **3.12**
- acceso a PowerShell

No se recomienda usar Python 3.14 para una instalacion nueva de este proyecto. Puede funcionar en algunas tareas, pero la version recomendada para evitar errores es **Python 3.12**.

### 2.2. Como comprobarlo

Abre PowerShell y ejecuta:

```powershell
git --version
python --version
```

El resultado esperado es:

- Git responde con una version instalada.
- Python responde con `3.11.x` o `3.12.x`.

Si alguno falla, instala primero ese componente antes de continuar.

## 3. Descargar una copia limpia del proyecto

Tienes dos formas validas.

### Opcion A. Clonar con Git

1. Crea o elige una carpeta vacia de trabajo.
2. Abre PowerShell en esa carpeta.
3. Ejecuta:

```powershell
git clone https://github.com/IngenioSoy26/pin_platform.git
cd pin_platform
```

### Opcion B. Descargar ZIP desde GitHub

1. Abre el repositorio en GitHub.
2. Pulsa `Code`.
3. Pulsa `Download ZIP`.
4. Descomprime el archivo.
5. Renombra la carpeta descomprimida a `pin_platform` si trae otro nombre.
6. Abre PowerShell dentro de esa carpeta.

### Verificacion del paso

Ejecuta:

```powershell
dir
```

Debes ver, al menos:

- `manage.py`
- `requirements.txt`
- `requirements-full.txt`
- `apps`
- `config`
- `docs`

Si no aparece `manage.py`, no estas en la carpeta correcta.

## 4. Crear un entorno virtual nuevo

Desde la raiz del proyecto ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
```

### Verificacion del paso

Cuando el entorno esta activo, PowerShell suele mostrar `(.venv)` al inicio de la linea.

Ademas, puedes comprobarlo con:

```powershell
python --version
where.exe python
```

La ruta de Python debe apuntar a `.venv`.

## 5. Elegir el tipo de instalacion

## Ruta 1. Instalacion recomendada y mas facil: SQLite

Esta es la ruta que debe seguir cualquier persona que quiera una instalacion limpia, rapida y reproducible.

### 5.1. Instalar dependencias minimas

Ejecuta:

```powershell
python -m pip install -r requirements.txt
```

### 5.2. Crear el archivo `.env`

En la raiz del proyecto crea un archivo llamado `.env` con este contenido:

```env
DB_ENGINE=sqlite
DEBUG=True
SECRET_KEY=dev-secret-key-pin-platform
ALLOWED_HOSTS=127.0.0.1,localhost
LANGUAGE_CODE=es-co
TIME_ZONE=America/Bogota
```

### 5.3. Verificar configuracion

Ejecuta:

```powershell
python manage.py check
```

El resultado esperado es:

```text
System check identified no issues (0 silenced).
```

### 5.4. Crear la base de datos

Ejecuta:

```powershell
python manage.py migrate
```

Este paso crea la base local en SQLite y aplica todas las migraciones.

### 5.5. Crear un usuario administrador

Ejecuta:

```powershell
python manage.py createsuperuser
```

Completa:

- nombre de usuario;
- correo, si lo deseas;
- contrasena.

### 5.6. Arrancar el servidor

Ejecuta:

```powershell
python manage.py runserver
```

Si todo salio bien, veras algo parecido a:

```text
Starting development server at http://127.0.0.1:8000/
```

### 5.7. Probar en el navegador

Abre:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/admin/`
- `http://127.0.0.1:8000/map/`
- `http://127.0.0.1:8000/dashboards/resumen/`

### 5.8. Que significa "instalacion exitosa"

Puedes considerar exitosa la instalacion minima si:

1. `python manage.py check` no devuelve errores;
2. `python manage.py migrate` termina correctamente;
3. `python manage.py runserver` arranca sin cortar;
4. puedes abrir la pagina principal y el admin en el navegador.

## Ruta 2. Instalacion completa con PostgreSQL/PostGIS

Usa esta ruta solo cuando necesites funciones geoespaciales completas o una configuracion mas cercana a despliegue real.

## 6. Requisitos extra para la ruta completa

Necesitas:

- PostgreSQL instalado
- PostGIS instalado
- una base de datos creada previamente

La recomendacion para Windows es instalar PostgreSQL en su ruta habitual:

- `C:\Program Files\PostgreSQL\<version>\`

El proyecto intenta detectar automaticamente la carpeta `bin` de PostgreSQL para encontrar `libpq.dll`. Si tu instalacion esta en otra ruta, deberas definir la variable `POSTGRES_BIN`.

## 7. Instalar dependencias completas

Con el entorno virtual activo, ejecuta:

```powershell
python -m pip install -r requirements-full.txt
```

Importante:

- esta instalacion es mas pesada;
- la recomendacion real para esta ruta es usar Python 3.12;
- algunas librerias geoespaciales tardan mas en instalarse.

## 8. Crear la base de datos en PostgreSQL

En PostgreSQL crea una base vacia, por ejemplo:

- nombre: `truck_routes_db`
- usuario: `postgres`
- puerto: `5432`

Despues activa PostGIS en esa base:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## 9. Crear el archivo `.env` para PostgreSQL/PostGIS

Crea o reemplaza el archivo `.env` con este contenido:

```env
DB_ENGINE=postgis
ENABLE_GIS=True
DEBUG=True
SECRET_KEY=dev-secret-key-pin-platform
ALLOWED_HOSTS=127.0.0.1,localhost
LANGUAGE_CODE=es-co
TIME_ZONE=America/Bogota

DB_NAME=truck_routes_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

Si PostgreSQL no esta instalado en la ruta habitual, agrega tambien:

```env
POSTGRES_BIN=C:\Program Files\PostgreSQL\17\bin
```

Ajusta la ruta segun tu version real.

## 10. Comprobar la configuracion completa

Ejecuta:

```powershell
python manage.py check
python manage.py migrate
```

Si ambos pasos terminan bien, la parte base de la instalacion completa ya esta lista.

## 11. Cargar datos operativos opcionales

La aplicacion puede arrancar sin ETL, pero varios dashboards y vistas dependen de datos cargados en la base.

### 11.1. Colocar archivos de datos

Si tienes datasets del proyecto, colocalos en:

- `data/`
- `dataset/`

Segun la configuracion real del proyecto:

- `DATA_DIR` apunta por defecto a `data/`
- `DATASET_DIR` apunta por defecto a `dataset/`

### 11.2. Ejecutar ETL

Si ya tienes los archivos necesarios:

```powershell
python manage.py cargar_datos_csv
```

Si estan en otra carpeta:

```powershell
python manage.py cargar_datos_csv --dir "C:\ruta\absoluta\a\mis_datasets"
```

### 11.3. Sincronizacion HPMS opcional

Si tambien descargaste el archivo maestro de HPMS:

```powershell
python manage.py sync_hpms
```

Opciones adicionales:

```powershell
python manage.py sync_hpms --discover --limit 5
python manage.py sync_hpms --match
```

## 12. Checklist final de validacion

Una instalacion limpia puede darse por correcta cuando se cumplan todos estos puntos:

- `git clone` o descarga ZIP completados correctamente
- existe la carpeta `.venv`
- `python -m pip install -r requirements.txt` o `requirements-full.txt` termina sin error
- existe el archivo `.env`
- `python manage.py check` responde sin errores
- `python manage.py migrate` responde sin errores
- `python manage.py runserver` arranca
- el navegador abre la web en `http://127.0.0.1:8000/`
- el admin abre en `http://127.0.0.1:8000/admin/`

## 13. Errores frecuentes y solucion

### Error 1. `python` no se reconoce

Solucion:

1. instala Python;
2. marca la opcion para agregar Python al PATH;
3. cierra y vuelve a abrir PowerShell.

### Error 2. `git` no se reconoce

Solucion:

1. instala Git para Windows;
2. cierra y vuelve a abrir PowerShell;
3. comprueba con `git --version`.

### Error 3. El entorno virtual no se activa

Prueba:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts, usa:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Luego vuelve a intentar la activacion.

### Error 4. Falla `pip install`

Haz esta secuencia:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Si estas en la instalacion completa, usa Python 3.12 y vuelve a probar con `requirements-full.txt`.

### Error 5. `manage.py check` falla por configuracion de base de datos

Revisa el archivo `.env`.

Para una instalacion segura desde cero, usa primero:

```env
DB_ENGINE=sqlite
```

Eso evita problemas iniciales con PostgreSQL.

### Error 6. Error con `libpq.dll`

Esto solo aplica cuando usas PostgreSQL/PostGIS.

Solucion:

1. localiza la carpeta `bin` de PostgreSQL;
2. agrega en `.env` la variable:

```env
POSTGRES_BIN=C:\Program Files\PostgreSQL\17\bin
```

3. cierra y abre la terminal de nuevo.

### Error 7. El servidor arranca, pero algunas vistas no muestran datos

Eso no significa que la instalacion este mal.

Normalmente significa una de estas dos cosas:

- aun no ejecutaste ETL;
- la base esta vacia y los dashboards dependen de registros cargados.

### Error 8. El puerto 8000 ya esta ocupado

Arranca el servidor en otro puerto:

```powershell
python manage.py runserver 8001
```

## 14. Recomendacion final

Para que la instalacion sea realmente exitosa en cualquier equipo:

1. usa una carpeta nueva y vacia;
2. usa Python 3.12;
3. empieza con SQLite;
4. valida `check`, `migrate` y `runserver`;
5. solo despues pasa a PostgreSQL/PostGIS y al ETL completo.

## 15. Comandos minimos para copiar y pegar

Si solo quieres el camino mas seguro, usa exactamente esto desde PowerShell:

```powershell
git clone https://github.com/IngenioSoy26/pin_platform.git
cd pin_platform
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
@"
DB_ENGINE=sqlite
DEBUG=True
SECRET_KEY=dev-secret-key-pin-platform
ALLOWED_HOSTS=127.0.0.1,localhost
LANGUAGE_CODE=es-co
TIME_ZONE=America/Bogota
"@ | Set-Content .env
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
