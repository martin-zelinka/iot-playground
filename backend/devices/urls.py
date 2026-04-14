"""
URL configuration for devices app.
"""

from django.urls import path

from . import views

app_name = "devices"

urlpatterns = [
    # Devices list page (index)
    path("", views.devices_list, name="devices_list"),
    # Device detail page
    path("<str:client_id>/", views.device_detail_page, name="device_detail_page"),
    # Device shutdown action
    path("<str:client_id>/shutdown/", views.device_shutdown, name="device_shutdown"),
]
