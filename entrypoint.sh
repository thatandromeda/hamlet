#!/bin/bash
set -e

python3.6 manage.py migrate
python3.6 manage.py collectstatic --noinput
python3.6 manage.py compress

gunicorn hamlet.wsgi -b 0.0.0.0:8000 -w 2
