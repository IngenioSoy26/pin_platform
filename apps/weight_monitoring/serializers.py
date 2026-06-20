from rest_framework import serializers
from .models import WeightRegulation, AxleConfiguration, WeightInspection

class WeightRegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightRegulation
        fields = '__all__'

class AxleConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AxleConfiguration
        fields = '__all__'

class WeightInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightInspection
        fields = '__all__'
