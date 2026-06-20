from rest_framework import serializers
from .models import RecyclingCenter

class RecyclingCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecyclingCenter
        fields = '__all__'
