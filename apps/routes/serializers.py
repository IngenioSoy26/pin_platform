from rest_framework import serializers

from .models import HPMSInventorySource, HPMSRoadSegment, HighwayRoute


class HighwayRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighwayRoute
        fields = "__all__"


class HPMSInventorySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HPMSInventorySource
        fields = [
            "id",
            "state_name",
            "state_code",
            "api_url",
            "map_url",
            "is_active",
            "last_discovered_at",
            "last_successful_sync",
            "last_error",
        ]


class HPMSRoadSegmentSerializer(serializers.ModelSerializer):
    source_state = serializers.CharField(source="source.state_name", read_only=True)

    class Meta:
        model = HPMSRoadSegment
        fields = [
            "id",
            "segment_key",
            "source_state",
            "state_name",
            "county_name",
            "route_name",
            "route_number",
            "route_type",
            "functional_class",
            "is_nhs",
            "is_interstate",
            "length_miles",
            "iri",
            "roughness_class",
            "surface_type",
            "pavement_type",
            "aadt",
            "truck_aadt",
            "lane_count",
            "mid_latitude",
            "mid_longitude",
            "year_recorded",
            "data_quality_score",
        ]
