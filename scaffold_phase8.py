import os

base_dir = r"c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\apps"

apps_to_create = {
    "alerts": {
        "models.py": """from django.db import models
from apps.devices.models import Truck, TireSensor

class Alert(models.Model):
    ALERT_TYPES = [
        ('LOW_PRESSURE', 'Presión Baja'),
        ('HIGH_PRESSURE', 'Presión Alta'),
        ('HIGH_TEMPERATURE', 'Temperatura Alta'),
        ('PUNCTURE', 'Pinchazo'),
        ('TIRE_WEAR_WARNING', 'Advertencia Desgaste'),
        ('TIRE_WEAR_CRITICAL', 'Desgaste Crítico'),
        ('SENSOR_OFFLINE', 'Sensor Desconectado'),
        ('LOW_BATTERY_SENSOR', 'Batería Baja (Sensor)'),
        ('LOW_BATTERY_MASTER', 'Batería Baja (Maestro)'),
        ('HARD_BRAKING', 'Frenazo Brusco'),
        ('HARD_ACCELERATION', 'Aceleración Brusca'),
        ('HOS_WARNING', 'Advertencia HOS'),
        ('HOS_VIOLATION', 'Violación HOS'),
        ('OVERWEIGHT_AXLE', 'Exceso Peso Eje'),
        ('OVERWEIGHT_GROSS', 'Exceso Peso Bruto'),
    ]
    SEVERITY_CHOICES = [
        ('INFO', 'Información'),
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Activa'),
        ('ACKNOWLEDGED', 'Reconocida'),
        ('RESOLVED', 'Resuelta'),
    ]

    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='system_alerts')
    sensor = models.ForeignKey(TireSensor, on_delete=models.SET_NULL, null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=15, choices=SEVERITY_CHOICES)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    trigger_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    
    location = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.truck.plate}"
""",
        "services.py": """from .models import Alert

class AlertEngine:
    @staticmethod
    def create_alert(truck, alert_type, severity, title, message, sensor=None, **kwargs):
        alert = Alert.objects.create(
            truck=truck,
            sensor=sensor,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            **kwargs
        )
        return alert
        
    @staticmethod
    def check_tire_alerts(reading):
        pass # To be implemented
        
    @staticmethod
    def check_hos_alerts(driver):
        pass # To be implemented
        
    @staticmethod
    def check_weight_alerts(truck):
        pass # To be implemented
"""
    },
    "recommendations": {
        "models.py": """from django.db import models
from apps.devices.models import Truck
from apps.alerts.models import Alert

class Recommendation(models.Model):
    REC_TYPES = [
        ('TIRE_SHOP', 'Tienda de Llantas'),
        ('REST_STOP', 'Parada de Descanso'),
        ('RESTAURANT', 'Restaurante'),
        ('FUEL_STATION', 'Estación de Combustible'),
        ('ALT_FUEL', 'Combustible Alternativo'),
        ('RECYCLING_CENTER', 'Centro de Reciclaje'),
        ('WIM_STATION', 'Estación WIM'),
        ('HOTEL', 'Hotel'),
        ('MECHANIC', 'Mecánico'),
    ]
    STATUS_CHOICES = [
        ('GENERATED', 'Generada'),
        ('SENT', 'Enviada al Conductor'),
        ('ACCEPTED', 'Aceptada'),
        ('REJECTED', 'Rechazada'),
        ('COMPLETED', 'Completada'),
    ]

    alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendations')
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='recommendations')
    rec_type = models.CharField(max_length=20, choices=REC_TYPES)
    priority = models.IntegerField(default=5) # 1-10
    
    target_name = models.CharField(max_length=255)
    target_address = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    distance_km = models.FloatField(null=True, blank=True)
    estimated_time_min = models.IntegerField(null=True, blank=True)
    estimated_cost_usd = models.FloatField(null=True, blank=True)
    
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='GENERATED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recomendación: {self.get_rec_type_display()} para {self.truck.plate}"
""",
        "services.py": """class RecommendationEngine:
    @staticmethod
    def generate_recommendations(alert):
        pass # To be implemented
"""
    },
    "iot_ingestion": {
        "models.py": """# Ingestión directa a modelos de devices y tires
""",
        "views.py": """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from apps.devices.models import MasterDevice, VehicleReading, TireSensor
from apps.tires.models import TireReading
from apps.alerts.services import AlertEngine
import json

class IoTReadingIngestionView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        device_code = data.get('device_code')
        
        try:
            master_device = MasterDevice.objects.get(device_code=device_code)
        except MasterDevice.DoesNotExist:
            return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)
            
        truck = master_device.truck
        v_data = data.get('vehicle_data', {})
        
        # Save VehicleReading
        VehicleReading.objects.create(
            master_device=master_device,
            timestamp=data.get('timestamp', timezone.now()),
            latitude=v_data.get('latitude'),
            longitude=v_data.get('longitude'),
            speed_mph=v_data.get('speed_mph'),
            heading=v_data.get('heading'),
            battery_level=v_data.get('battery_level', 100),
            signal_strength=v_data.get('signal_strength')
        )
        
        # Update Truck location
        if v_data.get('latitude') and v_data.get('longitude'):
            truck.current_latitude = v_data.get('latitude')
            truck.current_longitude = v_data.get('longitude')
            truck.save()
            
        # Process TireReadings
        tire_readings_data = data.get('tire_readings', [])
        for tr_data in tire_readings_data:
            position = tr_data.get('position')
            try:
                sensor = TireSensor.objects.get(master_device=master_device, position=position)
                reading = TireReading.objects.create(
                    sensor=sensor,
                    timestamp=data.get('timestamp', timezone.now()),
                    pressure_psi=tr_data.get('pressure_psi'),
                    temperature_f=tr_data.get('temperature_f'),
                    vibration_g=tr_data.get('vibration_g', 0.0),
                    battery_level=tr_data.get('battery_level', 100)
                )
                
                # Check alerts
                if tr_data.get('pressure_psi', 100) < 80:
                    AlertEngine.create_alert(
                        truck=truck,
                        alert_type='LOW_PRESSURE',
                        severity='HIGH',
                        title=f"Presión Baja en {position}",
                        message=f"La llanta {position} tiene {tr_data.get('pressure_psi')} PSI.",
                        sensor=sensor,
                        trigger_value=tr_data.get('pressure_psi'),
                        threshold_value=80.0
                    )
                    
            except TireSensor.DoesNotExist:
                pass
                
        return Response({'status': 'success', 'message': 'Data ingested successfully'}, status=status.HTTP_201_CREATED)
""",
        "urls.py": """from django.urls import path
from .views import IoTReadingIngestionView

urlpatterns = [
    path('reading/', IoTReadingIngestionView.as_view(), name='iot_reading_ingestion'),
]
"""
    }
}

for app, files in apps_to_create.items():
    app_dir = os.path.join(base_dir, app)
    os.makedirs(app_dir, exist_ok=True)
    
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        pass
        
    with open(os.path.join(app_dir, "apps.py"), "w") as f:
        f.write(f'''from django.apps import AppConfig\n\nclass {app.capitalize().replace('_', '')}Config(AppConfig):\n    default_auto_field = 'django.db.models.BigAutoField'\n    name = 'apps.{app}'\n''')
        
    for filename, content in files.items():
        with open(os.path.join(app_dir, filename), "w", encoding='utf-8') as f:
            f.write(content)
            
    # Create empty files for missing standard django files
    for empty_file in ['admin.py', 'serializers.py', 'views.py', 'urls.py', 'services.py']:
        filepath = os.path.join(app_dir, empty_file)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                if empty_file == 'urls.py':
                    f.write("from django.urls import path\n\nurlpatterns = []\n")
                else:
                    pass

print("Phase 8 apps created.")