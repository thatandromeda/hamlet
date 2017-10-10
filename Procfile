release: python manage.py migrate
web: gunicorn hamlet.wsgi --worker-class gevent --log-file -
