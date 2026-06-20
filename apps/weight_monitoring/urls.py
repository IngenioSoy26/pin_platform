from django.urls import path
from . import views

app_name = 'weight_monitoring'

urlpatterns = [
    path('dashboard/', views.WeightDashboardView.as_view(), name='dashboard'),
]