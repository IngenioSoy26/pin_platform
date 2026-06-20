from rest_framework import serializers
from .models import HighwayRoute

class HighwayRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighwayRoute
        fields = '__all__'
