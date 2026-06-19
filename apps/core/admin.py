from django.contrib import admin
from .models import Amenity, CarrierCompany, Location, TruckStop, WIMStation, AlternativeFuelStation, TireShop, RecyclingFacility, TransportationStatistic

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name', 'category')
    list_filter = ('category',)

@admin.register(CarrierCompany)
class CarrierCompanyAdmin(admin.ModelAdmin):
    list_display = ('dot_number', 'legal_name', 'carrier_operation', 'status')
    search_fields = ('dot_number', 'legal_name', 'dba_name')
    list_filter = ('status', 'carrier_operation')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'latitude', 'longitude')
    search_fields = ('name', 'city', 'state')
    list_filter = ('state',)
    filter_horizontal = ('amenities',)

@admin.register(TruckStop)
class TruckStopAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'parking_spaces')
    list_filter = ('state',)
    search_fields = ('name', 'city')
    filter_horizontal = ('amenities',)

@admin.register(WIMStation)
class WIMStationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'state', 'status')
    list_filter = ('status', 'state')
    search_fields = ('station_id', 'name')

@admin.register(AlternativeFuelStation)
class AlternativeFuelStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'fuel_type_code', 'state', 'is_public')
    list_filter = ('fuel_type_code', 'is_public', 'state')
    search_fields = ('name', 'city')

@admin.register(TireShop)
class TireShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'state', 'is_24_hours')
    list_filter = ('is_24_hours', 'state', 'brand')
    search_fields = ('name', 'city', 'brand')

@admin.register(RecyclingFacility)
class RecyclingFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'tires_recycled_tons', 'population_served')
    search_fields = ('name', 'city', 'state')
    list_filter = ('state',)

@admin.register(TransportationStatistic)
class TransportationStatisticAdmin(admin.ModelAdmin):
    list_display = ('date', 'highway_fatalities', 'truck_employment', 'diesel_price')
    date_hierarchy = 'date'
    ordering = ('-date',)
