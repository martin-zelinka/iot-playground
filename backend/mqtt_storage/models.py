from django.db import models


class MQTTPacket(models.Model):
    """Raw MQTT packet storage for all received messages."""
    topic = models.CharField(max_length=512, db_index=True)
    payload = models.JSONField(default=dict)
    qos = models.IntegerField(default=0)
    retain = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-received_at']
        verbose_name = "MQTT Packet"
        verbose_name_plural = "MQTT Packets"
        indexes = [
            models.Index(fields=['topic', '-received_at']),
            models.Index(fields=['received_at']),
        ]

    def __str__(self):
        return f"{self.topic} @ {self.received_at}"


class MQTTClientStatus(models.Model):
    """MQTT client status and connection tracking."""
    client_id = models.CharField(max_length=255, unique=True, db_index=True)
    client_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default='unknown')  # online, offline, error
    last_seen = models.DateTimeField(auto_now=True, db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Statistics
    total_packets = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)

    class Meta:
        ordering = ['-last_seen']
        verbose_name = "MQTT Client Status"
        verbose_name_plural = "MQTT Client Statuses"

    def __str__(self):
        return f"{self.client_id} - {self.status}"
