from django.contrib import admin
from apps.weight_monitoring.models import WeightRegulation, AxleConfiguration, WeightInspection

@admin.register(WeightRegulation)
class WeightRegulationAdmin(admin.ModelAdmin):
    list_display = ('state', 'state_name', 'federal_gross_limit', 'state_gross_limit', 'single_axle_limit', 'tandem_axle_limit')
    search_fields = ('state', 'state_name')
    list_filter = ('permits_available',)

@admin.register(AxleConfiguration)
class AxleConfigurationAdmin(admin.ModelAdmin):
    list_display = ('truck', 'axle_number', 'axle_type', 'position_ft', 'tire_count', 'current_weight')
    search_fields = ('truck__plate',)
    list_filter = ('axle_type',)

@admin.register(WeightInspection)
class WeightInspectionAdmin(admin.ModelAdmin):
    list_display = ('truck', 'timestamp', 'inspection_type', 'gross_weight', 'is_overweight')
    search_fields = ('truck__plate', 'location')
    list_filter = ('inspection_type', 'is_overweight', 'state')