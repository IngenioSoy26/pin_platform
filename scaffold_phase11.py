import os

base_dir = r"c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\apps\dashboards"
templates_dir = r"c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\templates\dashboards"

os.makedirs(base_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# 1. Crear init y apps.py
with open(os.path.join(base_dir, "__init__.py"), "w") as f: pass
with open(os.path.join(base_dir, "apps.py"), "w") as f:
    f.write("""from django.apps import AppConfig

class DashboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboards'
""")

# 2. Crear views.py
views_content = """from django.views.generic import TemplateView

class ResumenView(TemplateView):
    template_name = 'dashboards/resumen.html'

class MonitoreoIoTView(TemplateView):
    template_name = 'dashboards/monitoreo_iot.html'

class AlertasView(TemplateView):
    template_name = 'dashboards/alertas.html'

class HOSComplianceView(TemplateView):
    template_name = 'dashboards/hos_compliance.html'

class DesgasteLlantasView(TemplateView):
    template_name = 'dashboards/desgaste_llantas.html'

class PesoVehiculoView(TemplateView):
    template_name = 'dashboards/peso_vehiculo.html'

class RecomendacionesView(TemplateView):
    template_name = 'dashboards/recomendaciones.html'

class GeoespacialView(TemplateView):
    template_name = 'dashboards/geoespacial.html'

class EstacionesDescansoView(TemplateView):
    template_name = 'dashboards/estaciones_descanso.html'

class CombustibleReciclajeView(TemplateView):
    template_name = 'dashboards/combustible_reciclaje.html'

class RegulacionSeguridadView(TemplateView):
    template_name = 'dashboards/regulacion_seguridad.html'

class ModelosPredictivosView(TemplateView):
    template_name = 'dashboards/modelos_predictivos.html'
"""
with open(os.path.join(base_dir, "views.py"), "w", encoding="utf-8") as f:
    f.write(views_content)

# 3. Crear urls.py
urls_content = """from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('resumen/', views.ResumenView.as_view(), name='resumen'),
    path('iot/', views.MonitoreoIoTView.as_view(), name='monitoreo_iot'),
    path('alertas/', views.AlertasView.as_view(), name='alertas'),
    path('hos/', views.HOSComplianceView.as_view(), name='hos_compliance'),
    path('llantas/', views.DesgasteLlantasView.as_view(), name='desgaste_llantas'),
    path('peso/', views.PesoVehiculoView.as_view(), name='peso_vehiculo'),
    path('recomendaciones/', views.RecomendacionesView.as_view(), name='recomendaciones'),
    path('geoespacial/', views.GeoespacialView.as_view(), name='geoespacial'),
    path('estaciones/', views.EstacionesDescansoView.as_view(), name='estaciones_descanso'),
    path('combustible/', views.CombustibleReciclajeView.as_view(), name='combustible_reciclaje'),
    path('regulacion/', views.RegulacionSeguridadView.as_view(), name='regulacion_seguridad'),
    path('predictivos/', views.ModelosPredictivosView.as_view(), name='modelos_predictivos'),
]
"""
with open(os.path.join(base_dir, "urls.py"), "w", encoding="utf-8") as f:
    f.write(urls_content)

# 4. Crear plotly_charts.py (stub)
with open(os.path.join(base_dir, "plotly_charts.py"), "w", encoding="utf-8") as f:
    f.write("# Funciones para generar gráficos interactivos con Plotly\n")

# 5. Crear los 12 templates HTML base con Glassmorphism
templates = [
    "resumen.html", "monitoreo_iot.html", "alertas.html", "hos_compliance.html",
    "desgaste_llantas.html", "peso_vehiculo.html", "recomendaciones.html",
    "geoespacial.html", "estaciones_descanso.html", "combustible_reciclaje.html",
    "regulacion_seguridad.html", "modelos_predictivos.html"
]

template_base = """{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 style="color: var(--text-color); font-weight: 600; margin: 0;">
            <i class="fa-solid fa-chart-line text-info"></i> TITULO_REEMPLAZO
        </h2>
    </div>

    <div class="row">
        <div class="col-12">
            <div class="map-controls-panel p-5 text-center" style="min-height: 400px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <i class="fa-solid fa-person-digging mb-4" style="font-size: 4rem; color: #3b82f6; opacity: 0.8;"></i>
                <h3 style="color: var(--text-color);">Módulo en Construcción</h3>
                <p style="color: var(--text-muted); max-width: 500px; margin: 0 auto;">
                    Esta vista formará parte del panel interactivo con gráficos Plotly y mapas Leaflet.
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

for tpl in templates:
    title = tpl.replace(".html", "").replace("_", " ").title()
    content = template_base.replace("TITULO_REEMPLAZO", title)
    with open(os.path.join(templates_dir, tpl), "w", encoding="utf-8") as f:
        f.write(content)

print("Dashboards app scaffolded successfully.")
