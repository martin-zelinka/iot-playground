"""
Views for devices app.
Provides web pages for viewing MQTT client devices and their data.
"""
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
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


@require_http_methods(["POST"])
def device_shutdown(request, client_id):
    """
    Send shutdown command to a specific MQTT client device.
    """
    try:
        from mqtt.client import MQTTClient

        # Create a temporary client for sending the shutdown command
        shutdown_client = MQTTClient(
            client_id=f"django_controller_{client_id}",
            host=settings.MQTT_BROKER["HOST"],
            port=settings.MQTT_BROKER["PORT"],
            listen_for_control=False  # Don't need to listen for control messages
        )

        if shutdown_client.connect():
            # Publish shutdown command to the device's control topic
            control_topic = f"device/control/{client_id}"
            shutdown_client.publish(control_topic, "shutdown")

            logger.info(f"Sent shutdown command to device: {client_id}")
            messages.success(request, f"Shutdown command sent to {client_id}")

            # Give the message time to be sent
            import time
            time.sleep(0.5)

            shutdown_client.disconnect()
        else:
            logger.error(f"Failed to connect to MQTT broker for shutdown: {client_id}")
            messages.error(request, f"Failed to send shutdown command to {client_id}")

    except Exception as e:
        logger.error(f"Error sending shutdown command to {client_id}: {e}")
        messages.error(request, f"Error: {str(e)}")

    # Redirect back to devices list
    return redirect('devices:devices_list')
