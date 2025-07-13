web: gunicorn debug_buddy.wsgi --log-file - --bind 0.0.0.0:${PORT:-8000}
release: python manage.py migrate
