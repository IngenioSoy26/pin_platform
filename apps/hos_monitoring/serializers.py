from rest_framework import serializers

from apps.hos_monitoring.models import Driver, DriverLog, HOSAlert, HOSCompliance


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = "__all__"


class DriverLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLog
        fields = "__all__"


class HOSComplianceSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)

    class Meta:
        model = HOSCompliance
        fields = "__all__"


class HOSAlertSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)

    class Meta:
        model = HOSAlert
        fields = "__all__"
