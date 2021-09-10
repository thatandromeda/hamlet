import logging
import os
import sys

import requests

from .base import *  # noqa
from gensim.models.doc2vec import Doc2Vec

logger = logging.getLogger(__name__)

# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['RDS_DB_NAME'],
        'USER': os.environ['RDS_USERNAME'],
        'PASSWORD': os.environ['RDS_PASSWORD'],
        'HOST': os.environ['RDS_HOSTNAME'],
        'PORT': os.environ['RDS_PORT'],
    }
}


# GENERAL CONFIGURATION
# -----------------------------------------------------------------------------

# Get secret key from env variable
SECRET_KEY = os.environ['SECRET_KEY']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = [
    'hamlet.andromedayelton.com',
    'hamletenv2021small-env.eba-dpvfh2yj.us-east-2.elasticbeanstalk.com'
]


# Append Local EC2 IP to ALLOWED_HOSTS.
LOCAL_IP = None
try:
    LOCAL_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4',  # noqa
        timeout=0.01).text
except requests.exceptions.RequestException:
    logger.exception('Could not find local IP for AWS instance.')
    pass
if LOCAL_IP and not DEBUG:
    ALLOWED_HOSTS.append(LOCAL_IP)

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = 'hamlet.andromedayelton.com'
SESSION_COOKIE_SECURE = True


# STATIC FILE CONFIGURATION
# -----------------------------------------------------------------------------

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'hamlet.settings.storage.WhiteNoiseStaticFilesStorage'

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Model files are stored on s3.
# MODELS_DIR is an env variable defined in eb as /models.
MODELS_DIR = os.environ.get('MODELS_DIR')
MODEL_FILE = os.path.join(MODELS_DIR, 'hamlet.model')
NEURAL_NET = Doc2Vec.load(MODEL_FILE)


# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'brief': {
            'format': '%(asctime)s %(levelname)s %(name)s[%(funcName)s]: %(message)s',  # noqa
        },
    },
    'handlers': {
        'console_info': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        },
    },
    'loggers': {
        '': {
            'handlers': ['console_info'],
            'level': 'INFO',
        }
    }
}

# Will be emailed by the management command about API usage.
ADMINS = [('Andromeda Yelton', 'andromeda.yelton@gmail.com')]
