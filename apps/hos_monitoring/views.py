from django.views.generic import ListView
from apps.hos_monitoring.models import Driver, HOSCompliance, HOSAlert
from django.db.models import Count, Q

class HOSDashboardView(ListView):
    model = Driver
    template_name = 'hos_monitoring/dashboard.html'
    context_object_name = 'drivers'

    def get_queryset(self):
        # Seleccionamos relacionados para evitar queries N+1
        return Driver.objects.filter(status='ACTIVE').select_related('hos_compliance').prefetch_related('hos_alerts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener métricas globales
        total_drivers = Driver.objects.filter(status='ACTIVE').count()
        compliant_drivers = HOSCompliance.objects.filter(driver__status='ACTIVE', is_compliant=True).count()
        violation_drivers = total_drivers - compliant_drivers
        
        active_alerts = HOSAlert.objects.filter(status='ACTIVE')
        
        context['total_drivers'] = total_drivers
        context['compliant_drivers'] = compliant_drivers
        context['violation_drivers'] = violation_drivers
        context['active_alerts_count'] = active_alerts.count()
        
        # Alertas recientes para mostrar en la interfaz
        context['recent_alerts'] = active_alerts.order_by('-timestamp')[:10]
        
        return context