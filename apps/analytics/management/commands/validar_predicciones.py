from django.core.management.base import BaseCommand
from apps.analytics.models import Prediction
from apps.analytics.validators import validate_prediction

class Command(BaseCommand):
    help = 'Valida predicciones contra datos reales (Backtesting)'

    def handle(self, *args, **kwargs):
        unvalidated = Prediction.objects.filter(is_validated=False)
        count = unvalidated.count()
        for p in unvalidated:
            validate_prediction(p)
        self.stdout.write(self.style.SUCCESS(f"Se validaron {count} predicciones con los datos actuales."))
