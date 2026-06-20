from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from apps.fleet.models import Trip
from apps.devices.models import Truck
from apps.hos_monitoring.models import Driver
from apps.fleet.forms import TripForm, DriverForm, TruckForm

class FleetDashboardView(ListView):
    model = Trip
    template_name = 'fleet/dashboard.html'
    context_object_name = 'trips'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas rápidas para el dashboard
        context['total_trips'] = Trip.objects.count()
        context['active_trips'] = Trip.objects.filter(status='IN_TRANSIT').count()
        context['pending_trips'] = Trip.objects.filter(status='PENDING').count()
        return context

class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'fleet/trip_form.html'
    success_url = reverse_lazy('fleet:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, "Viaje asignado y creado exitosamente.")
        return super().form_valid(form)

class TripUpdateView(UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'fleet/trip_form.html'
    success_url = reverse_lazy('fleet:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, "El viaje ha sido actualizado.")
        return super().form_valid(form)

# Vistas para Conductores
class DriverListView(ListView):
    model = Driver
    template_name = 'fleet/driver_list.html'
    context_object_name = 'drivers'

class DriverCreateView(CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'fleet/driver_form.html'
    success_url = reverse_lazy('fleet:driver_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Conductor registrado exitosamente.")
        return super().form_valid(form)

# Vistas para Tractomulas
class TruckListView(ListView):
    model = Truck
    template_name = 'fleet/truck_list.html'
    context_object_name = 'trucks'

class TruckCreateView(CreateView):
    model = Truck
    form_class = TruckForm
    template_name = 'fleet/truck_form.html'
    success_url = reverse_lazy('fleet:truck_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Tractomula registrada exitosamente.")
        return super().form_valid(form)