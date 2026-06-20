from rest_framework.views import APIView
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
