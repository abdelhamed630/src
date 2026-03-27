#!/bin/sh
set -e

echo "⏳ Waiting for database..."
until python -c "
import os, psycopg2
try:
    psycopg2.connect(
        host=os.environ['DATABASE_HOST'],
        port=os.environ.get('DATABASE_PORT', '5432'),
        dbname=os.environ['DATABASE_NAME'],
        user=os.environ['DATABASE_USER'],
        password=os.environ['DATABASE_PASSWORD'],
        connect_timeout=3,
    )
    print('✅ Database ready')
except Exception as e:
    exit(1)
"; do
  echo "  DB not ready yet, retrying in 2s..."
  sleep 2
done

echo "📦 Running migrations..."
python manage.py migrate --noinput

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🚀 Starting Gunicorn..."
exec gunicorn E_Commerce.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
