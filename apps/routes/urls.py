from django.urls import path

from .views import (
    HPMSSRoughnessGeoJSONAPIView,
    HPMSSegmentListAPIView,
    HPMSSourceListAPIView,
    HPMSSummaryAPIView,
)

app_name = "routes"

urlpatterns = [
    path("hpms/summary/", HPMSSummaryAPIView.as_view(), name="hpms_summary"),
    path("hpms/sources/", HPMSSourceListAPIView.as_view(), name="hpms_sources"),
    path("hpms/segments/", HPMSSegmentListAPIView.as_view(), name="hpms_segments"),
    path("hpms/roughness-geojson/", HPMSSRoughnessGeoJSONAPIView.as_view(), name="hpms_roughness_geojson"),
]
