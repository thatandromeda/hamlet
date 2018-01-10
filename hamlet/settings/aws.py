import os
import sys

from .base import *  # noqa
from gensim.models.doc2vec import Doc2Vec


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
#GET SECRET KEY FROM ENV VARIABLE
SECRET_KEY = os.environ ['SECRET_KEY']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


ALLOWED_HOSTS = [
    '.us-east-1.elasticbeanstalk.com',
    '52.87.98.36',
    '52.7.74.114', #Load balancer IP's we (Andy?) should revisit 
    '.compute-1.amazonaws.com', # allows viewing of instances directly
    'mitlibraries-hamlet.mit.edu',
    'localhost',
 ]

# Apped Local EC2 IP to allowed hosts so Load Balancer is denied
# ----------------------------------------------------------------------------
import requests
LOCAL_IP = None
try:
    LOCAL_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4', timeout=0.01).text
except requests.exceptions.RequestException:
    pass
if LOCAL_IP and not DEBUG:
    ALLOWED_HOSTS.append(LOCAL_IP)

# STATIC FILE CONFIGURATION
# -----------------------------------------------------------------------------

MIDDLEWARE.insert(1,'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_URL = '/static/'
STATIC_ROOT =  os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

#MODEL FILES STORED ON S3
#MODELS_DIR IS AN ENV VARIABLE DEFINED IN EB AS /models
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
ADMINS = [('Andromeda Yelton', 'm31@mit.edu')]
