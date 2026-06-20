from rest_framework import serializers
from .models import WIMStation, SizeWeightRegulation

class WIMStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WIMStation
        fields = '__all__'

class SizeWeightRegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeWeightRegulation
        fields = '__all__'
