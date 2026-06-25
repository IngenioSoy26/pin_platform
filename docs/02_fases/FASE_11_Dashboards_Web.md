# Fase 11: Dashboards Web

## Resumen
Esta fase consolidó la capa de visualización web de PIN Platform. El objetivo era convertir los datos operativos, geoespaciales, normativos e IoT en una experiencia navegable para análisis, supervisión y toma de decisiones.

## Objetivo de la fase
- Implementar dashboards web con Bootstrap, Plotly y Leaflet.
- Cubrir las áreas críticas del reto mediante páginas temáticas.
- Unificar KPIs, tablas, mapas y gráficos en una navegación coherente.

## Componentes implementados

### 1. Estructura de vistas
Se centralizó la lógica web en `apps/dashboards/views.py` y `apps/dashboards/urls.py`, con plantillas en `templates/dashboards/`.

### 2. Páginas temáticas
Se identifican 12 dashboards principales implementados en la carpeta de templates:

1. `resumen.html`
2. `monitoreo_iot.html`
3. `alertas.html`
4. `hos_compliance.html`
5. `desgaste_llantas.html`
6. `peso_vehiculo.html`
7. `recomendaciones.html`
8. `geoespacial.html`
9. `estaciones_descanso.html`
10. `combustible_reciclaje.html`
11. `regulacion_seguridad.html`
12. `modelos_predictivos.html`

Adicionalmente, existe `hub.html` como punto de acceso general a la analítica.

## Aportes funcionales de la fase

### Dashboard de resumen
- KPIs globales de flota.
- Mapa operativo y estado general del sistema.

### Dashboard IoT
- Monitoreo de sensores, telemetría histórica y consola de streaming.
- Vista de flota y gemelo digital para inspección.

### Dashboards normativos
- HOS y cumplimiento.
- Peso vehicular, WIM y seguridad.

### Dashboards operativos
- Alertas y recomendaciones.
- Estaciones de descanso, combustible y reciclaje.
- Vista geoespacial con amenidades, clima, cierres y soporte de corredores.

### Dashboard predictivo
- KPIs de analítica predictiva.
- Riesgo de falla, dispersión de desgaste y tabla de componentes en riesgo.

## Tecnologías usadas
- Django Templates
- Bootstrap
- Plotly
- Leaflet
- JavaScript para interacción y simulación visual

## Resultado de la fase
La plataforma quedó con una capa visual amplia y defendible académicamente, cubriendo los dominios más importantes del reto mediante dashboards temáticos reutilizables y enlazados entre sí.

## Estado real de cumplimiento
- La fase está implementada funcionalmente.
- Varias páginas fueron refinadas posteriormente durante la estabilización del proyecto.
- Algunas vistas se apoyan en fallback o simulación cuando la base no dispone de datos recientes suficientes, pero la estructura de analítica web sí quedó construida.
