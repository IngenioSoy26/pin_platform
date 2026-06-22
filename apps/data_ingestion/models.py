from django.db import models
from django.utils import timezone
import os

class DataSource(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Dataset")
    file_path = models.CharField(max_length=500, verbose_name="Ruta del Archivo (Local o S3)")
    file_type = models.CharField(max_length=50, choices=[('CSV', 'CSV'), ('GEOJSON', 'GeoJSON'), ('EXCEL', 'Excel')], default='CSV')
    schema = models.JSONField(blank=True, null=True, verbose_name="Esquema/Estructura Esperada")
    last_load = models.DateTimeField(null=True, blank=True, verbose_name="Última Carga Exitosa")
    
    class Meta:
        verbose_name = "Fuente de Datos"
        verbose_name_plural = "Fuentes de Datos"
        
    def __str__(self):
        return self.name

class ETLJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('RUNNING', 'En Ejecución'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    dataset = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    records_processed = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_log = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Trabajo ETL"
        verbose_name_plural = "Trabajos ETL"
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.dataset.name} - {self.status}"

