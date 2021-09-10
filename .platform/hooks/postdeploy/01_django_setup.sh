#!/bin/bash
# See https://github.com/aws/elastic-beanstalk-roadmap/issues/68 ,
# https://github.com/aws/elastic-beanstalk-roadmap/issues/15 .

source /var/app/venv/*/bin/activate
cd /var/app/current
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compress
