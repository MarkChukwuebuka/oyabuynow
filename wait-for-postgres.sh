#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z $PGHOST $PGPORT; do
  sleep 1
done

echo "PostgreSQL started"

# Run migrations
python manage.py makemigrations --no-input
python manage.py migrate --no-input

# Start Gunicorn
gunicorn --bind 0.0.0.0:8000 core.wsgi:application
