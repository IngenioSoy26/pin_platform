from django.db import models

class Carrier(models.Model):
    dot_number = models.CharField(max_length=50, unique=True)
    legal_name = models.CharField(max_length=255)
    dba_name = models.CharField(max_length=255, null=True, blank=True)
    entity_type = models.CharField(max_length=100, null=True, blank=True)
    num_power_units = models.IntegerField(default=0)
    num_drivers = models.IntegerField(default=0)
    state = models.CharField(max_length=2)

    def __str__(self):
        return self.legal_name

class MonthlyTransportIndicator(models.Model):
    date = models.DateField()
    indicator_name = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    region = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.indicator_name} - {self.date}"
