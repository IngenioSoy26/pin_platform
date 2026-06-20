from django.contrib import admin
from .models import WIMStation, SizeWeightRegulation

@admin.register(WIMStation)
class WIMStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'station_code', 'direction')
    search_fields = ('name', 'station_code')

@admin.register(SizeWeightRegulation)
class SizeWeightRegulationAdmin(admin.ModelAdmin):
    list_display = ('state', 'max_weight_lbs', 'max_length_ft')
    search_fields = ('state',)
