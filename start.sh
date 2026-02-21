#!/bin/bash

# Exit on error
set -e

# Run database migrations
python manage.py migrate --noinput

# Collect static files (for Whitenoise)
python manage.py collectstatic --noinput --clear

# Create superuser ONLY if CREATE_SUPERUSER=1 is set in Render env vars
if [ "$CREATE_SUPERUSER" = "1" ]; then
    echo "🔐 Creating superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Superuser 'admin' created (password: 'admin')")
else:
    print("ℹ️ Superuser 'admin' already exists")
EOF
fi

# Start Gunicorn (production server)
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 60