from django.urls import path
from . import views

app_name = 'hos_monitoring'

urlpatterns = [
    path('dashboard/', views.HOSDashboardView.as_view(), name='dashboard'),
]