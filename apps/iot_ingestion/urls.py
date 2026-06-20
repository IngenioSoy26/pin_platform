from django.urls import path
from .views import IoTReadingIngestionView

urlpatterns = [
    path('reading/', IoTReadingIngestionView.as_view(), name='iot_reading_ingestion'),
]
