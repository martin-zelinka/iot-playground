#!/bin/bash
set -e

echo "Running Django migrations..."
uv run backend/manage.py migrate --noinput

echo "Starting Django server..."
exec uv run backend/manage.py runserver 0.0.0.0:8000
