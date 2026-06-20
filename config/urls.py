"""Root URL configuration for PIN Platform."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from apps.core.views import api_routes, dashboard_view, map_view, api_locations, api_live_dashboard

def home(request):
    return render(request, "home.html")

def login_view(request):
    return render(request, "login.html")

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("api/dashboard/live/", api_live_dashboard, name="api_live_dashboard"),
    path("api/dashboards/resumen/live/", api_live_dashboard, name="api_live_resumen"),
    path("login/", login_view, name="login"),
    path("map/", map_view, name="map"),
    path("api/locations/", api_locations, name="api_locations"),
    path("api/routes/", api_routes, name="api_routes"),
    path("admin/", admin.site.urls),
    path("fleet/", include("apps.fleet.urls")),
    path("hos/", include("apps.hos_monitoring.urls")),
    path("weight/", include("apps.weight_monitoring.urls")),
    path("api/iot/", include("apps.iot_ingestion.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
