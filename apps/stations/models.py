from django.db import models

class TruckStation(models.Model):
    name = models.CharField(max_length=255)
    operator = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    
    # Amenities (Cruciales para la toma de decisiones del conductor)
    has_diesel = models.BooleanField(default=False)
    has_def = models.BooleanField(default=False)
    has_restaurant = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_showers = models.BooleanField(default=False)
    has_tires = models.BooleanField(default=False) # Para emergencias de llantas
    has_mechanic = models.BooleanField(default=False)
    
    parking_spaces = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class TruckStopParking(models.Model):
    station = models.ForeignKey(TruckStation, on_delete=models.CASCADE, related_name='parking_details', null=True, blank=True)
    name = models.CharField(max_length=255)
    total_spots = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
