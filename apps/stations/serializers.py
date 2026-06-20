from rest_framework import serializers
from .models import TruckStation, TruckStopParking

class TruckStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckStation
        fields = '__all__'

class TruckStopParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckStopParking
        fields = '__all__'
