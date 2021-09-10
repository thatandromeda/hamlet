# The syntax differs at
# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html ,
# but deploying with that causes errors in Procfile parsing.
web: gunicorn hamlet.wsgi --worker-class gevent --log-file -
