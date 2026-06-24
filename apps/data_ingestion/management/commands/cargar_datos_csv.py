from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import os
import glob
from apps.data_ingestion.models import DataSource, ETLJob
from apps.data_ingestion.etl import run_etl_job

class Command(BaseCommand):
    help = 'Carga los 15 datasets operativos desde la carpeta data a la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default=str(settings.DATA_DIR),
            help='Directorio donde se encuentran los datasets operativos (default: settings.DATA_DIR)'
        )

    def handle(self, *args, **options):
        data_dir = options['dir']
        
        self.stdout.write(self.style.SUCCESS(f"Iniciando ETL para los 15 datasets desde '{data_dir}'..."))
        
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.WARNING(f"El directorio '{data_dir}' no existe. Por favor, coloque los archivos allí o use --dir <ruta>"))
            # Crear la carpeta data/ de ejemplo
            os.makedirs(data_dir, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f"Se ha creado el directorio '{data_dir}'. Coloque sus archivos CSV/Excel/GeoJSON allí y vuelva a ejecutar."))
            return

        # Lista de archivos en el directorio
        files = glob.glob(os.path.join(data_dir, '*.*'))
        valid_extensions = ['.csv', '.xlsx', '.xls', '.geojson']
        data_files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]
        
        if not data_files:
            self.stdout.write(self.style.WARNING(f"No se encontraron archivos con formato válido en '{data_dir}'."))
            return

        self.stdout.write(self.style.SUCCESS(f"Se encontraron {len(data_files)} archivos para procesar."))
        
        for file_path in data_files:
            file_name = os.path.basename(file_path)
            self.stdout.write(f"\nProcesando: {file_name}")
            
            ext = os.path.splitext(file_name)[1].upper().replace('.', '')
            
            # 1. Crear o actualizar DataSource
            source, created = DataSource.objects.update_or_create(
                name=file_name,
                defaults={
                    'file_path': file_path,
                    'file_type': ext if ext in ['CSV', 'GEOJSON', 'EXCEL'] else 'CSV'
                }
            )
            
            # 2. Crear ETLJob
            job = ETLJob.objects.create(
                dataset=source,
                status='PENDING'
            )
            
            # 3. Ejecutar ETL
            self.stdout.write("  -> Ejecutando motor ETL...")
            run_etl_job(job)
            
            # 4. Refrescar job para ver estado final
            job.refresh_from_db()
            
            if job.status == 'COMPLETED':
                self.stdout.write(self.style.SUCCESS(f"  -> Completado exitosamente. Logs:\n{job.error_log}"))
            else:
                self.stdout.write(self.style.ERROR(f"  -> Fallido. Logs de error:\n{job.error_log}"))
                
        self.stdout.write(self.style.SUCCESS("\n¡ETL operativo ejecutado por completo!"))
