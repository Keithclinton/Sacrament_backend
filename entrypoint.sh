#!/bin/sh
set -e
python manage.py migrate --noinput
exec gunicorn config.wsgi --bind 0.0.0.0:$PORT --log-file -
