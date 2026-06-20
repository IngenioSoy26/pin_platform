from django.core.management.base import BaseCommand
from apps.analytics.training_manager import TrainingManager

class Command(BaseCommand):
    help = 'Entrena los 6 modelos de Machine Learning'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cargando datasets históricos...")
        success = TrainingManager.train_all_models()
        if success:
            self.stdout.write(self.style.SUCCESS("Todos los modelos fueron entrenados y guardados en ml_models/ exitosamente."))
