from django.contrib import admin
from .models import RecyclingCenter

@admin.register(RecyclingCenter)
class RecyclingCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'recycling_type', 'accepts_tires', 'capacity_tons')
    list_filter = ('accepts_tires',)
    search_fields = ('name',)
