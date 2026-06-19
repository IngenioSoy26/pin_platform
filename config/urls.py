"""Root URL configuration for PIN Platform."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from apps.core.views import map_view, api_locations, api_routes

def home(request):
    return render(request, "home.html")

def dashboard(request):
    return render(request, "dashboard.html")

def login_view(request):
    return render(request, "login.html")

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("login/", login_view, name="login"),
    path("map/", map_view, name="map"),
    path("api/locations/", api_locations, name="api_locations"),
    path("api/routes/", api_routes, name="api_routes"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
