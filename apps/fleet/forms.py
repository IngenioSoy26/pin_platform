from django import forms
from apps.fleet.models import Trip

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
