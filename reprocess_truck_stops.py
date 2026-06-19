import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.data_ingestion.models import DatasetUpload
from apps.data_ingestion.etl import process_uploaded_dataset

print("Iniciando reprocesamiento de Truck Stops...")
truck_stops_uploads = DatasetUpload.objects.filter(dataset_type='TRUCK_STOPS', status='COMPLETED')

for ds in truck_stops_uploads:
    print(f"Reprocesando: {ds.file.name}")
    process_uploaded_dataset(ds)
    print(f"Listo: {ds.file.name}")

print("Reprocesamiento finalizado con éxito.")
