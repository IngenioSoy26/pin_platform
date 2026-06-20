from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    path('dashboard/', views.FleetDashboardView.as_view(), name='dashboard'),
    path('trip/new/', views.TripCreateView.as_view(), name='trip_create'),
    path('trip/<int:pk>/update/', views.TripUpdateView.as_view(), name='trip_update'),
    path('drivers/', views.DriverListView.as_view(), name='driver_list'),
    path('drivers/new/', views.DriverCreateView.as_view(), name='driver_create'),
    path('trucks/', views.TruckListView.as_view(), name='truck_list'),
    path('trucks/new/', views.TruckCreateView.as_view(), name='truck_create'),
]