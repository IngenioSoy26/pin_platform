from django.db import models

class WIMStation(models.Model):
    name = models.CharField(max_length=255)
    station_code = models.CharField(max_length=50, unique=True)
    direction = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class SizeWeightRegulation(models.Model):
    state = models.CharField(max_length=2, unique=True)
    max_weight_lbs = models.FloatField(default=80000.0)
    max_length_ft = models.FloatField(default=65.0)
    max_width_in = models.FloatField(default=102.0)
    max_height_ft = models.FloatField(default=13.5)

    def __str__(self):
        return f"Regulaciones {self.state}"
