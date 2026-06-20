from rest_framework import serializers
from .models import AlternativeFuelStation

class AlternativeFuelStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternativeFuelStation
        fields = '__all__'
