"""
Views for devices app.
Provides web pages for viewing MQTT client devices and their data.
"""
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from bson import json_util
import json
import logging


logger = logging.getLogger(__name__)


def _serialize_document(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    return json.loads(json_util.dumps(doc))


@require_http_methods(["GET"])
def devices_list(request):
    """
    Display a web page with a table of all MQTT client devices.
    """
    try:
        from .models import MQTTClientStatus

        devices = MQTTClientStatus.objects.all()
        online_count = devices.filter(status='online').count()

        return render(request, 'devices/index.html', {
            'devices': devices,
            'online_count': online_count
        })

    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return render(request, 'devices/index.html', {'devices': [], 'online_count': 0})


@require_http_methods(["GET"])
def device_detail_page(request, client_id):
    """
    Display a web page with MongoDB data for a specific client.
    """
    try:
        from django_api.mongo.mongodb_client import get_device_data

        # Fetch device data from MongoDB using client_id as source
        device_data = get_device_data(source=client_id, limit=100, skip=0)
        serialized_data = [_serialize_document(doc) for doc in device_data]

        return render(request, 'devices/detail.html', {
            'client_id': client_id,
            'device_data': serialized_data
        })

    except Exception as e:
        logger.error(f"Error fetching device data for {client_id}: {e}")
        return render(request, 'devices/detail.html', {
            'client_id': client_id,
            'device_data': []
        })
