"""
URL configuration for devices app.
"""
from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # List all device data with optional filtering
    path('devices/', views.device_data_list, name='device_data_list'),

    # Get latest data for a specific source
    path('devices/<str:source>/latest/', views.device_data_detail, name='device_data_detail'),

    # Create new device data
    path('devices/create/', views.device_data_create, name='device_data_create'),
]
