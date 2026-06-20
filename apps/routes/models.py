from django.db import models

class HighwayRoute(models.Model):
    route_id = models.CharField(max_length=100, unique=True)
    route_name = models.CharField(max_length=255)
    route_type = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    length_km = models.FloatField(default=0.0)

    def __str__(self):
        return self.route_name
