from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    path('dashboard/', views.FleetDashboardView.as_view(), name='dashboard'),
    path('trip/new/', views.TripCreateView.as_view(), name='trip_create'),
    path('trip/<int:pk>/update/', views.TripUpdateView.as_view(), name='trip_update'),
]