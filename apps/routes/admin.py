from django.contrib import admin

from .models import (
    HPMSConditionSnapshot,
    HPMSFieldCatalog,
    HPMSInventorySource,
    HPMSLayerCatalog,
    HPMSRoadSegment,
    HighwayRoute,
    RouteSegmentMatch,
)


@admin.register(HighwayRoute)
class HighwayRouteAdmin(admin.ModelAdmin):
    list_display = ("route_id", "route_name", "state", "length_km", "is_active")
    search_fields = ("route_name", "route_id", "state")
    list_filter = ("state", "is_active")


@admin.register(HPMSInventorySource)
class HPMSInventorySourceAdmin(admin.ModelAdmin):
    list_display = ("state_name", "state_code", "is_active", "last_discovered_at", "last_successful_sync")
    search_fields = ("state_name", "state_code")
    list_filter = ("is_active",)


@admin.register(HPMSLayerCatalog)
class HPMSLayerCatalogAdmin(admin.ModelAdmin):
    list_display = ("source", "layer_id", "layer_name", "geometry_type", "supports_query", "record_count")
    search_fields = ("source__state_name", "layer_name")
    list_filter = ("supports_query", "geometry_type")


@admin.register(HPMSFieldCatalog)
class HPMSFieldCatalogAdmin(admin.ModelAdmin):
    list_display = ("layer", "field_name", "field_type", "is_candidate_iri", "is_candidate_surface", "is_candidate_aadt")
    search_fields = ("field_name", "field_alias", "layer__layer_name", "layer__source__state_name")
    list_filter = ("is_candidate_iri", "is_candidate_surface", "is_candidate_aadt")


@admin.register(HPMSRoadSegment)
class HPMSRoadSegmentAdmin(admin.ModelAdmin):
    list_display = ("segment_key", "state_name", "route_number", "iri", "roughness_class", "is_nhs", "is_interstate")
    search_fields = ("segment_key", "route_name", "route_number", "state_name", "county_name")
    list_filter = ("state_name", "roughness_class", "is_nhs", "is_interstate")


@admin.register(HPMSConditionSnapshot)
class HPMSConditionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("segment", "year", "iri", "roughness_class", "condition_score")
    search_fields = ("segment__segment_key", "segment__route_name", "segment__route_number")
    list_filter = ("year", "roughness_class")


@admin.register(RouteSegmentMatch)
class RouteSegmentMatchAdmin(admin.ModelAdmin):
    list_display = ("highway_route", "hpms_segment", "match_method", "overlap_ratio", "is_primary_match")
    search_fields = ("highway_route__route_name", "highway_route__route_id", "hpms_segment__segment_key")
    list_filter = ("match_method", "is_primary_match")
