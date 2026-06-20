from django.db import models
from apps.devices.models import Truck

class Prediction(models.Model):
    MODEL_CHOICES = [
        ('TIRE_WEAR', 'Tire Wear Predictor'),
        ('TIRE_FAILURE', 'Tire Failure Predictor'),
        ('HOS_COMPLIANCE', 'HOS Compliance Predictor'),
        ('OVERWEIGHT_RISK', 'Overweight Risk Predictor'),
        ('DEMAND_FORECAST', 'Demand Forecaster'),
        ('LOCATION_OPTIMIZER', 'Optimal Location Recommender'),
    ]
    
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, null=True, blank=True, related_name='predictions')
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    prediction_data = models.JSONField(verbose_name="Resultados de la Predicción")
    confidence_score = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_model_name_display()} - {self.timestamp.date()}"
