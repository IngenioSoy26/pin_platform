from django.contrib import admin
from .models import AlternativeFuelStation

@admin.register(AlternativeFuelStation)
class AlternativeFuelStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'fuel_type', 'is_hd_fuel')
    list_filter = ('fuel_type', 'is_hd_fuel')
    search_fields = ('name',)
