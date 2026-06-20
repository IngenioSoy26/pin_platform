from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('', views.DashboardsHubView.as_view(), name='hub'),
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
