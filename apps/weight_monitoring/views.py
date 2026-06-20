from django.views.generic import ListView
from apps.devices.models import Truck
from apps.weight_monitoring.models import WeightInspection, WeightRegulation
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Max, Q

class WeightDashboardView(ListView):
    model = Truck
    template_name = 'weight_monitoring/dashboard.html'
    context_object_name = 'trucks'

    def get_queryset(self):
        return Truck.objects.filter(status='ACTIVE').prefetch_related('weight_inspections', 'axles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenemos inspecciones recientes (últimos 30 días)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_inspections = WeightInspection.objects.filter(timestamp__gte=thirty_days_ago)
        
        # Métricas principales
        context['total_inspections'] = recent_inspections.count()
        
        overweight_count = recent_inspections.filter(is_overweight=True).count()
        context['overweight_count'] = overweight_count
        
        # Porcentaje de cumplimiento
        if context['total_inspections'] > 0:
            context['compliance_rate'] = 100 - ((overweight_count / context['total_inspections']) * 100)
        else:
            context['compliance_rate'] = 100.0
            
        # Peso promedio registrado
        avg_weight = recent_inspections.aggregate(Avg('gross_weight'))['gross_weight__avg']
        context['avg_gross_weight'] = avg_weight if avg_weight else 0
        
        # Últimas inspecciones críticas (exceso de peso)
        context['critical_inspections'] = WeightInspection.objects.filter(
            is_overweight=True
        ).order_by('-timestamp')[:10]
        
        # Las últimas inspecciones en general
        context['latest_inspections'] = WeightInspection.objects.all().order_by('-timestamp')[:15]
        
        return context