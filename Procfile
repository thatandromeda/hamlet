# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html
web: gunicorn --bind :8000 hamlet.wsgi:application --worker-class gevent --log-file -
