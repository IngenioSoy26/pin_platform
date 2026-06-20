from django.contrib import admin
from .models import HighwayRoute

@admin.register(HighwayRoute)
class HighwayRouteAdmin(admin.ModelAdmin):
    list_display = ('route_id', 'route_name', 'state', 'length_km')
    search_fields = ('route_name', 'route_id', 'state')
    list_filter = ('state',)
