from django.contrib import admin
from apps.fleet.models import FleetManager, Trip

@admin.register(FleetManager)
class FleetManagerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'phone', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'company__legal_name')
    list_filter = ('is_active', 'company')

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'truck', 'driver', 'status', 'scheduled_start', 'origin_address', 'destination_address')
    search_fields = ('company__legal_name', 'truck__plate', 'driver__license_number', 'origin_address', 'destination_address')
    list_filter = ('status', 'company')
    date_hierarchy = 'scheduled_start'