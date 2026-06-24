from django.views.generic import TemplateView
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import DataSource, ETLJob
import threading
import os
import json
import urllib.request
from django.core.files.storage import FileSystemStorage


def _report_debug_event(hypothesis_id, location, msg, data=None):
    try:
        payload = {
            "sessionId": "etl-button-state",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "msg": msg,
            "data": data or {},
            "ts": __import__("time").time_ns() // 1_000_000,
        }
        urllib.request.urlopen(
            urllib.request.Request(
                "http://127.0.0.1:7777/event",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
        ).read()
    except Exception:
        pass

class ConfigDashboardView(TemplateView):
    template_name = 'data_ingestion/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        running_jobs_qs = ETLJob.objects.filter(status='RUNNING')
        
        context['total_sources'] = DataSource.objects.count()
        context['completed_jobs'] = ETLJob.objects.filter(status='COMPLETED').count()
        context['failed_jobs'] = ETLJob.objects.filter(status='FAILED').count()
        context['running_jobs'] = running_jobs_qs.count()
        context['is_etl_running'] = context['running_jobs'] > 0
        
        # Últimos 20 trabajos para conservar el historial operativo visible
        context['recent_jobs'] = ETLJob.objects.select_related('dataset').order_by('-started_at')[:20]
        
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
        valid_extensions = {'.csv', '.xlsx', '.xls', '.geojson'}
        data_dir = str(settings.DATA_DIR)
        os.makedirs(data_dir, exist_ok=True)
        available_files = [
            file_name
            for file_name in os.listdir(data_dir)
            if os.path.splitext(file_name)[1].lower() in valid_extensions
        ]

        # #region debug-point A:run-etl-entry
        _report_debug_event("A", "apps/data_ingestion/views.py:run_etl_api", "[DEBUG] run_etl_api received POST", {"method": request.method, "running_before": ETLJob.objects.filter(status='RUNNING').count(), "available_files": len(available_files)})
        # #endregion
        if not available_files:
            return JsonResponse({
                'status': 'error',
                'message': f'No hay archivos operativos en "{settings.DATA_DIR}". Sube o mueve los datasets a la carpeta data antes de ejecutar el ETL.',
            }, status=400)

        if ETLJob.objects.filter(status='RUNNING').exists():
            # #region debug-point C:run-etl-conflict
            _report_debug_event("C", "apps/data_ingestion/views.py:run_etl_api", "[DEBUG] run_etl_api rejected due to active job", {"running_jobs": ETLJob.objects.filter(status='RUNNING').count()})
            # #endregion
            return JsonResponse({
                'status': 'error',
                'message': 'Ya hay un ETL en ejecución. Espera a que termine antes de iniciarlo de nuevo.',
            }, status=409)

        def run_command():
            try:
                # #region debug-point B:thread-start
                _report_debug_event("B", "apps/data_ingestion/views.py:run_command", "[DEBUG] ETL background thread started", {"data_dir": str(settings.DATA_DIR)})
                # #endregion
                # Ejecuta el comando que creamos anteriormente
                call_command('cargar_datos_csv', dir=str(settings.DATA_DIR))
                # #region debug-point B:thread-finished
                _report_debug_event("B", "apps/data_ingestion/views.py:run_command", "[DEBUG] ETL background thread completed", {"latest_job_status": ETLJob.objects.order_by('-started_at').values_list('status', flat=True).first(), "latest_job_dataset": ETLJob.objects.select_related('dataset').order_by('-started_at').values_list('dataset__name', flat=True).first()})
                # #endregion
            except Exception as e:
                # #region debug-point B:thread-error
                _report_debug_event("B", "apps/data_ingestion/views.py:run_command", "[DEBUG] ETL background thread failed", {"error": str(e)})
                # #endregion
                print(f"Error crítico ejecutando ETL desde la UI: {e}")
        
        # Iniciamos el hilo en segundo plano
        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()
        # #region debug-point A:thread-launched
        _report_debug_event("A", "apps/data_ingestion/views.py:run_etl_api", "[DEBUG] ETL thread launched from API", {"thread_alive": thread.is_alive()})
        # #endregion
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Proceso ETL iniciado en segundo plano. Escaneando carpeta "{settings.DATA_DIR}".'
        })
        
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)


def etl_status_api(request):
    running_jobs_qs = ETLJob.objects.filter(status='RUNNING').select_related('dataset').order_by('-started_at')
    latest_job = ETLJob.objects.select_related('dataset').order_by('-started_at').first()
    # #region debug-point D:status-endpoint
    _report_debug_event("D", "apps/data_ingestion/views.py:etl_status_api", "[DEBUG] etl_status_api queried", {"running_jobs": running_jobs_qs.count(), "latest_status": latest_job.status if latest_job else None, "latest_dataset": latest_job.dataset.name if latest_job else None})
    # #endregion

    payload = {
        'is_running': running_jobs_qs.exists(),
        'running_jobs': running_jobs_qs.count(),
        'latest_job': None,
    }

    if latest_job:
        payload['latest_job'] = {
            'dataset': latest_job.dataset.name,
            'status': latest_job.status,
            'records_processed': latest_job.records_processed,
            'started_at': latest_job.started_at.isoformat(),
            'completed_at': latest_job.completed_at.isoformat() if latest_job.completed_at else None,
            'error_log': latest_job.error_log or '',
        }

    return JsonResponse(payload)

@csrf_exempt
def upload_dataset_api(request):
    """
    Endpoint para recibir y guardar archivos en la carpeta operativa configurada en settings.DATA_DIR.
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
            
        # Asegurar que el directorio de datasets exista
        data_dir = str(settings.DATA_DIR)
        os.makedirs(data_dir, exist_ok=True)
        
        fs = FileSystemStorage(location=data_dir)
        
        # Si el archivo ya existe, lo borramos para sobreescribirlo
        file_path = os.path.join(data_dir, uploaded_file.name)
        if fs.exists(uploaded_file.name):
            fs.delete(uploaded_file.name)
            
        filename = fs.save(uploaded_file.name, uploaded_file)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Archivo {filename} subido correctamente a {settings.DATA_DIR}.'
        })
        
    return JsonResponse({'status': 'error', 'message': 'No se encontró ningún archivo'}, status=400)
