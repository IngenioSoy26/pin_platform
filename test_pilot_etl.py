import os
import sys

try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
    django.setup()

    from apps.data_ingestion.models import DatasetUpload
    from apps.data_ingestion.etl import process_uploaded_dataset

    with open('debug_output_pilot.txt', 'w') as f:
        ds = DatasetUpload.objects.filter(dataset_type='TRUCK_STOPS').last()
        if ds:
            f.write(f"Encontrado: {ds.file.path}\n")
            process_uploaded_dataset(ds)
            f.write("Logs:\n")
            f.write(ds.processing_logs)
        else:
            f.write("No hay dataset TRUCK_STOPS\n")
except Exception as e:
    import traceback
    with open('debug_output_pilot.txt', 'w') as f:
        f.write("Error:\n")
        f.write(traceback.format_exc())
