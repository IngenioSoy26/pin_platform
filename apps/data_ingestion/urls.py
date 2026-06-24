from django.urls import path
from . import views

app_name = 'data_ingestion'

urlpatterns = [
    path('', views.ConfigDashboardView.as_view(), name='config_dashboard'),
    path('api/run-etl/', views.run_etl_api, name='run_etl_api'),
    path('api/etl-status/', views.etl_status_api, name='etl_status_api'),
    path('api/upload-dataset/', views.upload_dataset_api, name='upload_dataset_api'),
]
