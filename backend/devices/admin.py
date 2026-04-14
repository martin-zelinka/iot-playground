from django.contrib import admin

from .models import MQTTClientStatus


@admin.register(MQTTClientStatus)
class MQTTClientStatusAdmin(admin.ModelAdmin):
    """Admin interface for MQTT client status."""

    list_display = [
        "client_id",
        "client_type",
        "status",
        "last_seen",
        "first_seen",
        "total_packets",
        "total_errors",
    ]
    list_filter = ["status", "client_type", "last_seen"]
    search_fields = ["client_id", "client_type"]
    readonly_fields = ["first_seen", "last_seen"]
    ordering = ["-last_seen"]
