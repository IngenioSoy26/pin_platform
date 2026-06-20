from django import forms
from apps.fleet.models import Trip
from apps.devices.models import Truck
from apps.hos_monitoring.models import Driver

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'company', 'truck', 'driver', 
            'origin_address', 'destination_address', 
            'scheduled_start', 'scheduled_end', 'status'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control glass-input'}),
            'truck': forms.Select(attrs={'class': 'form-control glass-input'}),
            'driver': forms.Select(attrs={'class': 'form-control glass-input'}),
            'origin_address': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: Los Angeles, CA'}),
            'destination_address': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: Dallas, TX'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-control glass-input', 'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': 'form-control glass-input', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name} (CDL: {obj.license_number})"
        self.fields['truck'].label_from_instance = lambda obj: f"{obj.plate} - {obj.brand} {obj.model}"
        self.fields['company'].label_from_instance = lambda obj: f"{obj.legal_name} (DOT: {obj.dot_number})"
        # Evitar cargar millones de empresas en memoria. Solo mostramos las que tienen tractomulas registradas o la de prueba/simuladas.
        self.fields['company'].queryset = self.fields['company'].queryset.filter(
            id__in=Truck.objects.values('carrier_id').distinct()
        ) | self.fields['company'].queryset.filter(legal_name__icontains='Prueba') | self.fields['company'].queryset.filter(legal_name__icontains='[SIMULADO]')

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['first_name', 'last_name', 'license_number', 'license_state', 'cdl_class', 'hire_date', 'status']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: Juan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: Pérez'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: CDL1234567'}),
            'license_state': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: CA'}),
            'cdl_class': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: A'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ['vin', 'plate', 'brand', 'model', 'year', 'num_tires', 'carrier', 'status']
        widgets = {
            'vin': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'VIN de 17 caracteres'}),
            'plate': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: ABC-1234'}),
            'brand': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: Kenworth'}),
            'model': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ej: T680'}),
            'year': forms.NumberInput(attrs={'class': 'form-control glass-input'}),
            'num_tires': forms.NumberInput(attrs={'class': 'form-control glass-input'}),
            'carrier': forms.Select(attrs={'class': 'form-control glass-input'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.models import CarrierCompany
        test_company = CarrierCompany.objects.filter(legal_name__icontains='Prueba') | CarrierCompany.objects.filter(legal_name__icontains='[SIMULADO]')
        self.fields['carrier'].queryset = test_company if test_company.exists() else CarrierCompany.objects.all()[:50]
        self.fields['carrier'].label_from_instance = lambda obj: f"{obj.legal_name} (DOT: {obj.dot_number})"
