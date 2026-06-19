from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.hos_monitoring.models import Driver, DriverLog, HOSAlert, HOSCompliance
from apps.hos_monitoring.serializers import (
    DriverLogSerializer,
    DriverSerializer,
    HOSAlertSerializer,
    HOSComplianceSerializer,
)
from apps.hos_monitoring.services import HOSCalculator


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all().order_by("last_name", "first_name")
    serializer_class = DriverSerializer

    @action(detail=True, methods=["get"])
    def compliance(self, request, pk=None):
        driver = self.get_object()
        compliance, _ = HOSCompliance.objects.get_or_create(
            driver=driver,
            defaults={"cycle_start": driver.created_at},
        )
        return Response(HOSComplianceSerializer(compliance).data)

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        driver = self.get_object()
        HOSCalculator.update_hos_status(driver)
        alerts = HOSCalculator.generate_hos_alerts(driver)
        return Response(
            {
                "driver_id": driver.id,
                "is_compliant": driver.hos_compliance.is_compliant,
                "alerts_generated": HOSAlertSerializer(alerts, many=True).data,
            }
        )


class DriverLogViewSet(viewsets.ModelViewSet):
    queryset = DriverLog.objects.all().order_by("-timestamp")
    serializer_class = DriverLogSerializer


class HOSAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HOSAlert.objects.all().order_by("-timestamp")
    serializer_class = HOSAlertSerializer
