from django.db import models

class AlternativeFuelStation(models.Model):
    FUEL_TYPES = [
        ('CNG', 'Compressed Natural Gas'),
        ('LNG', 'Liquefied Natural Gas'),
        ('ELEC', 'Electric'),
        ('H2', 'Hydrogen'),
    ]
    name = models.CharField(max_length=255)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPES)
    is_hd_fuel = models.BooleanField(default=False, verbose_name="Heavy-Duty Ready")
    access_type = models.CharField(max_length=50, null=True, blank=True)
    operators = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.fuel_type})"
