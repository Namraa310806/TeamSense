#!/bin/bash
# Entry point script for backend
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -q; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding data..."
python manage.py seed_data

echo "Starting server..."
exec gunicorn teamsense.wsgi:application --bind 0.0.0.0:8000 --workers 3
