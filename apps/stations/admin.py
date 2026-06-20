from django.contrib import admin
from .models import TruckStation, TruckStopParking

@admin.register(TruckStation)
class TruckStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'operator', 'has_tires', 'has_mechanic', 'has_parking')
    search_fields = ('name', 'operator')
    list_filter = ('has_tires', 'has_mechanic', 'has_diesel')

    def has_parking(self, obj):
        return obj.parking_spaces > 0
    has_parking.boolean = True

@admin.register(TruckStopParking)
class TruckStopParkingAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'total_spots')
    search_fields = ('name',)
