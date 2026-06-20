from django.contrib import admin
from .models import Carrier, MonthlyTransportIndicator

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'dot_number', 'num_power_units', 'state')
    search_fields = ('legal_name', 'dot_number')
    list_filter = ('state',)

@admin.register(MonthlyTransportIndicator)
class MonthlyTransportIndicatorAdmin(admin.ModelAdmin):
    list_display = ('indicator_name', 'date', 'value', 'unit')
    search_fields = ('indicator_name',)
    list_filter = ('date',)
