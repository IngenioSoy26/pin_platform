from django.contrib import admin
from .models import DataSource, ETLJob

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_type', 'last_load')
    search_fields = ('name',)

@admin.register(ETLJob)
class ETLJobAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'status', 'records_processed', 'started_at', 'completed_at')
    list_filter = ('status', 'dataset')
