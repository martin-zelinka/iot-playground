"""
Views for devices app.
Provides endpoints for accessing device data from MongoDB.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import json_util
import json
import logging

logger = logging.getLogger(__name__)


def _serialize_document(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    return json.loads(json_util.dumps(doc))


@require_http_methods(["GET"])
def device_data_list(request):
    """
    Get all device data with optional filtering.

    Query parameters:
        - source: Filter by source (e.g., weather_publisher_5096)
        - limit: Maximum number of records to return (default: 100)
        - skip: Number of records to skip (default: 0)
    """
    try:
        from django_api.mongo.mongodb_client import get_device_data

        source = request.GET.get('source')
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))

        data = get_device_data(source=source, limit=limit, skip=skip)
        serialized_data = [_serialize_document(doc) for doc in data]

        return JsonResponse({
            'success': True,
            'count': len(serialized_data),
            'data': serialized_data
        })

    except Exception as e:
        logger.error(f"Error fetching device data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def device_data_detail(request, source):
    """
    Get the latest data for a specific source.

    Path parameters:
        - source: The source identifier (e.g., weather_publisher_5096)
    """
    try:
        from django_api.mongo.mongodb_client import get_latest_by_source

        doc = get_latest_by_source(source)

        if doc:
            return JsonResponse({
                'success': True,
                'data': _serialize_document(doc)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Source not found'
            }, status=404)

    except Exception as e:
        logger.error(f"Error fetching device data for {source}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def device_data_create(request):
    """
    Insert a new device data document.

    Expected JSON body:
        {
            "source": "weather_publisher_5096",
            "protocol": "mqtt",
            "payload": {
                "topic": "sensors/weather_publisher_5096/PRG/temperature",
                "message": {
                    "data": "..."
                }
            }
        }
    """
    try:
        from django_api.mongo.mongodb_client import insert_device_data
        from datetime import datetime

        data = json.loads(request.body)

        # Add received_at timestamp if not provided
        if 'received_at' not in data:
            data['received_at'] = datetime.utcnow()

        inserted_id = insert_device_data(data)

        return JsonResponse({
            'success': True,
            'inserted_id': str(inserted_id)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating device data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

