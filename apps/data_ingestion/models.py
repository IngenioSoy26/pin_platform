from django.db import models
import os

class DatasetUpload(models.Model):
    """
    Modelo para gestionar la subida de los archivos originales del gobierno
    o entidades (CSV, Excel, GeoJSON).
    Permite subir el archivo crudo y posteriormente procesarlo para actualizar
    la base de datos de 'core'.
    """
    
    DATASET_TYPES = [
        ('TRUCK_STOPS', 'Truck Stops (NTAD)'),
        ('WIM_STATIONS', 'WIM Stations (NTAD)'),
        ('TIRE_SHOPS', 'Tire Shops (OSM)'),
        ('ALT_FUEL', 'Alternative Fuel Stations'),
        ('RECYCLING', 'Recycling Infrastructure'),
        ('CARRIERS', 'Carrier Company Census'),
        ('STATS', 'Monthly Transportation Stats'),
        ('ENFORCEMENT', 'Truck Size & Weight Enforcement'),
        ('ROUTES_NHS', 'National Highway System (GeoJSON)'),
        ('OTHER', 'Otro / Sin clasificar'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de Procesamiento'),
        ('PROCESSING', 'Procesando...'),
        ('COMPLETED', 'Completado con Éxito'),
        ('FAILED', 'Fallido'),
    ]

    title = models.CharField(max_length=255, verbose_name="Título Descriptivo")
    dataset_type = models.CharField(max_length=50, choices=DATASET_TYPES, verbose_name="Tipo de Dataset")
    
    # El archivo se guardará en la carpeta media/datasets/año/mes/
    file = models.FileField(upload_to='datasets/%Y/%m/', verbose_name="Archivo Original (CSV/Excel/GeoJSON)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Estado ETL")
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Procesamiento")
    
    # Campo para guardar errores si el procesamiento de Pandas falla
    processing_logs = models.TextField(blank=True, null=True, verbose_name="Logs de Procesamiento")

    class Meta:
        verbose_name = "Subida de Dataset"
        verbose_name_plural = "Subidas de Datasets"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_dataset_type_display()} - {self.title}"

    def filename(self):
        return os.path.basename(self.file.name)
