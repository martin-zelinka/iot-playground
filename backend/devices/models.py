from django.db import models


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
