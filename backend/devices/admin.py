from django.contrib import admin
from .models import MQTTPacket, MQTTClientStatus


@admin.register(MQTTPacket)
class MQTTPacketAdmin(admin.ModelAdmin):
    """Admin interface for MQTT packets."""
    list_display = ['topic', 'payload_preview', 'qos', 'retain', 'received_at']
    list_filter = ['qos', 'retain', 'received_at']
    search_fields = ['topic', 'payload']
    readonly_fields = ['received_at']
    date_hierarchy = 'received_at'
    ordering = ['-received_at']

    def payload_preview(self, obj):
        """Show preview of JSON payload."""
        return str(obj.payload)[:100]
    payload_preview.short_description = 'Payload'


@admin.register(MQTTClientStatus)
class MQTTClientStatusAdmin(admin.ModelAdmin):
    """Admin interface for MQTT client status."""
    list_display = ['client_id', 'client_type', 'status', 'last_seen', 'first_seen', 'total_packets', 'total_errors']
    list_filter = ['status', 'client_type', 'last_seen']
    search_fields = ['client_id', 'client_type']
    readonly_fields = ['first_seen', 'last_seen']
    ordering = ['-last_seen']
