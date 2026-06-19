from django.contrib import admin
from .models import DatasetUpload
from .etl import process_uploaded_dataset

@admin.register(DatasetUpload)
class DatasetUploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'dataset_type', 'status', 'uploaded_at', 'processed_at')
    list_filter = ('dataset_type', 'status', 'uploaded_at')
    search_fields = ('title', 'processing_logs')
    readonly_fields = ('uploaded_at', 'processed_at', 'processing_logs')
    
    actions = ['process_dataset']

    @admin.action(description='Ejecutar Procesamiento ETL (Clase 8)')
    def process_dataset(self, request, queryset):
        for dataset in queryset:
            # En producción esto debería ir a Celery. 
            # Por ahora lo ejecutamos síncronamente para la maqueta.
            process_uploaded_dataset(dataset)
            
        self.message_user(request, f"Se procesaron {queryset.count()} datasets correctamente.")
