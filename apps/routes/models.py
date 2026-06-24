from django.db import models
from django.utils import timezone


class HighwayRoute(models.Model):
    route_id = models.CharField(max_length=100, unique=True)
    route_name = models.CharField(max_length=255)
    route_type = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    length_km = models.FloatField(default=0.0)
    route_geometry = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ruta Nacional"
        verbose_name_plural = "Rutas Nacionales"

    def __str__(self):
        return self.route_name


class HPMSInventorySource(models.Model):
    """
    Catálogo maestro de endpoints HPMS por estado.
    """

    state_name = models.CharField(max_length=100, unique=True)
    state_code = models.CharField(max_length=3, blank=True)
    api_url = models.URLField(max_length=500)
    map_url = models.URLField(max_length=500, blank=True)
    source_dataset = models.ForeignKey(
        "data_ingestion.DataSource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hpms_sources",
    )
    is_active = models.BooleanField(default=True)
    last_discovered_at = models.DateTimeField(null=True, blank=True)
    last_successful_sync = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Fuente HPMS"
        verbose_name_plural = "Fuentes HPMS"
        ordering = ["state_name"]

    def __str__(self):
        return self.state_name


class HPMSLayerCatalog(models.Model):
    """
    Capas detectadas dentro de un FeatureServer HPMS.
    """

    source = models.ForeignKey(HPMSInventorySource, on_delete=models.CASCADE, related_name="layers")
    layer_id = models.IntegerField()
    layer_name = models.CharField(max_length=255)
    geometry_type = models.CharField(max_length=100, blank=True)
    supports_query = models.BooleanField(default=False)
    record_count = models.IntegerField(default=0)
    last_schema_sync = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Capa HPMS"
        verbose_name_plural = "Capas HPMS"
        unique_together = ("source", "layer_id")
        ordering = ["source__state_name", "layer_id"]

    def __str__(self):
        return f"{self.source.state_name} - {self.layer_name}"


class HPMSFieldCatalog(models.Model):
    """
    Esquema normalizado por capa para detectar IRI, superficie y tráfico.
    """

    layer = models.ForeignKey(HPMSLayerCatalog, on_delete=models.CASCADE, related_name="fields")
    field_name = models.CharField(max_length=255)
    field_alias = models.CharField(max_length=255, blank=True)
    field_type = models.CharField(max_length=100, blank=True)
    is_nullable = models.BooleanField(default=True)
    is_candidate_iri = models.BooleanField(default=False)
    is_candidate_surface = models.BooleanField(default=False)
    is_candidate_aadt = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Campo HPMS"
        verbose_name_plural = "Campos HPMS"
        unique_together = ("layer", "field_name")
        ordering = ["layer", "field_name"]

    def __str__(self):
        return f"{self.layer.layer_name}::{self.field_name}"


class HPMSRoadSegment(models.Model):
    """
    Segmento vial HPMS unificado para analítica operativa en PIN.
    """

    segment_key = models.CharField(max_length=200, unique=True)
    source = models.ForeignKey(HPMSInventorySource, on_delete=models.SET_NULL, null=True, blank=True, related_name="segments")
    layer = models.ForeignKey(HPMSLayerCatalog, on_delete=models.SET_NULL, null=True, blank=True, related_name="segments")
    external_segment_id = models.CharField(max_length=255, blank=True)
    source_record_id = models.CharField(max_length=255, blank=True)
    state_name = models.CharField(max_length=100, blank=True)
    county_name = models.CharField(max_length=100, blank=True)
    route_name = models.CharField(max_length=255, blank=True)
    route_number = models.CharField(max_length=100, blank=True)
    route_type = models.CharField(max_length=100, blank=True)
    functional_class = models.CharField(max_length=100, blank=True)
    is_nhs = models.BooleanField(default=False)
    is_interstate = models.BooleanField(default=False)
    urban_code = models.CharField(max_length=100, blank=True)
    start_measure = models.FloatField(null=True, blank=True)
    end_measure = models.FloatField(null=True, blank=True)
    length_miles = models.FloatField(null=True, blank=True)
    iri = models.FloatField(null=True, blank=True)
    roughness_class = models.CharField(max_length=50, blank=True)
    surface_type = models.CharField(max_length=100, blank=True)
    pavement_type = models.CharField(max_length=100, blank=True)
    aadt = models.IntegerField(null=True, blank=True)
    truck_aadt = models.IntegerField(null=True, blank=True)
    lane_count = models.IntegerField(null=True, blank=True)
    mid_latitude = models.FloatField(null=True, blank=True)
    mid_longitude = models.FloatField(null=True, blank=True)
    year_recorded = models.IntegerField(null=True, blank=True)
    geometry_json = models.JSONField(null=True, blank=True)
    raw_attributes = models.JSONField(default=dict, blank=True)
    data_quality_score = models.FloatField(default=0.0)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Segmento HPMS"
        verbose_name_plural = "Segmentos HPMS"
        ordering = ["state_name", "route_number", "segment_key"]
        indexes = [
            models.Index(fields=["state_name", "route_number"]),
            models.Index(fields=["state_name", "iri"]),
            models.Index(fields=["is_nhs", "is_interstate"]),
        ]

    def __str__(self):
        label = self.route_number or self.route_name or self.segment_key
        return f"{self.state_name} - {label}"


class HPMSConditionSnapshot(models.Model):
    """
    Historial simplificado por segmento y año para comparar evolución.
    """

    segment = models.ForeignKey(HPMSRoadSegment, on_delete=models.CASCADE, related_name="condition_snapshots")
    year = models.IntegerField()
    iri = models.FloatField(null=True, blank=True)
    iri_unit = models.CharField(max_length=50, default="in/mi")
    roughness_class = models.CharField(max_length=50, blank=True)
    surface_type = models.CharField(max_length=100, blank=True)
    pavement_type = models.CharField(max_length=100, blank=True)
    aadt = models.IntegerField(null=True, blank=True)
    truck_aadt = models.IntegerField(null=True, blank=True)
    lane_count = models.IntegerField(null=True, blank=True)
    condition_score = models.FloatField(default=0.0)
    data_quality_score = models.FloatField(default=0.0)
    measured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Snapshot HPMS"
        verbose_name_plural = "Snapshots HPMS"
        unique_together = ("segment", "year")
        ordering = ["-year", "segment__state_name"]

    def __str__(self):
        return f"{self.segment.segment_key} - {self.year}"


class RouteSegmentMatch(models.Model):
    """
    Relación entre una ruta interna del sistema y un segmento HPMS.
    """

    highway_route = models.ForeignKey(HighwayRoute, on_delete=models.CASCADE, related_name="hpms_matches")
    hpms_segment = models.ForeignKey(HPMSRoadSegment, on_delete=models.CASCADE, related_name="route_matches")
    match_method = models.CharField(max_length=100, default="heuristic")
    overlap_ratio = models.FloatField(default=0.0)
    distance_meters = models.FloatField(null=True, blank=True)
    is_primary_match = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Match Ruta-HPMS"
        verbose_name_plural = "Matches Ruta-HPMS"
        unique_together = ("highway_route", "hpms_segment")
        ordering = ["highway_route__route_name", "-is_primary_match"]

    def __str__(self):
        return f"{self.highway_route.route_name} -> {self.hpms_segment.segment_key}"
