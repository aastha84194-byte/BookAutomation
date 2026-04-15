#!/bin/bash

# --- BookAutomation Startup Script ---
# Orchestrates Django and Celery in a single Render container.

echo ">>> Applying database migrations..."
python manage.py migrate --noinput

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Starting Gunicorn (Web Service)..."
# Start gunicorn in the background
# We use 0.0.0.0:$PORT because Render sets the PORT env var.
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 &

echo ">>> Starting Celery (Background Worker)..."
# Start celery in the foreground to keep the container alive.
# pool=prefork is better for Linux.
# --concurrency=1 is crucial for Free Tier memory (512MB).
celery -A config worker --loglevel=info --pool=prefork --concurrency=1
