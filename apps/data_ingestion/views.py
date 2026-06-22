from django.views.generic import TemplateView
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from .models import DataSource, ETLJob
import threading
import os
from django.core.files.storage import FileSystemStorage

class ConfigDashboardView(TemplateView):
    template_name = 'data_ingestion/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_sources'] = DataSource.objects.count()
        context['completed_jobs'] = ETLJob.objects.filter(status='COMPLETED').count()
        context['failed_jobs'] = ETLJob.objects.filter(status='FAILED').count()
        context['running_jobs'] = ETLJob.objects.filter(status='RUNNING').count()
        
        # Últimos 10 trabajos
        context['recent_jobs'] = ETLJob.objects.select_related('dataset').order_by('-started_at')[:10]
        
        # Fuentes de datos
        context['sources'] = DataSource.objects.all().order_by('-last_load')
        
        return context

@csrf_exempt
def run_etl_api(request):
    """
    Endpoint para disparar el comando de ETL desde la UI de configuración.
    Se ejecuta en un hilo separado (background) para no bloquear la respuesta HTTP.
    """
    if request.method == 'POST':
        def run_command():
            try:
                # Ejecuta el comando que creamos anteriormente
                call_command('cargar_datos_csv', dir='data')
            except Exception as e:
                print(f"Error crítico ejecutando ETL desde la UI: {e}")
        
        # Iniciamos el hilo en segundo plano
        thread = threading.Thread(target=run_command)
        thread.start()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Proceso ETL iniciado en segundo plano. Escaneando carpeta "data/".'
        })
        
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)

@csrf_exempt
def upload_dataset_api(request):
    """
    Endpoint para recibir y guardar archivos en la carpeta 'data/'.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        
        # Validar extensión
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls', '.geojson']:
            return JsonResponse({
                'status': 'error', 
                'message': 'Formato no soportado. Usa CSV, Excel o GeoJSON.'
            }, status=400)
            
        # Asegurar que el directorio data/ exista
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        fs = FileSystemStorage(location=data_dir)
        
        # Si el archivo ya existe, lo borramos para sobreescribirlo
        file_path = os.path.join(data_dir, uploaded_file.name)
        if fs.exists(uploaded_file.name):
            fs.delete(uploaded_file.name)
            
        filename = fs.save(uploaded_file.name, uploaded_file)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Archivo {filename} subido correctamente a la carpeta data/.'
        })
        
    return JsonResponse({'status': 'error', 'message': 'No se encontró ningún archivo'}, status=400)