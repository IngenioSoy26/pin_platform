from rest_framework import serializers
from .models import Carrier, MonthlyTransportIndicator

class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = '__all__'
