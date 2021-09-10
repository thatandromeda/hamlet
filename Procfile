# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html
web: gunicorn --bind 0.0.0.0:8000 --worker-class gevent --log-file - hamlet.wsgi:application
