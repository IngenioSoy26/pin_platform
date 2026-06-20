from django.db import models

class RecyclingCenter(models.Model):
    name = models.CharField(max_length=255)
    capacity_tons = models.FloatField(null=True, blank=True)
    recycling_type = models.CharField(max_length=100)
    accepts_tires = models.BooleanField(default=False, verbose_name="Acepta Llantas Usadas") # Vital para sostenibilidad PIN
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
