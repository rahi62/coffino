#!/bin/sh
set -eu

# In the single-backend Coolify deployment, apply committed migrations before
# Gunicorn accepts traffic. Never generate migrations at runtime.
# Set CAF_INO_RUN_MIGRATIONS=0 only when migrations are managed separately.
if [ "${CAF_INO_RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
