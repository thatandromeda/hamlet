import os
import sys

from .base import *  # noqa
from gensim.models.doc2vec import Doc2Vec

# CHECK FOR EC2 TO ADD IP TO ALLOWED HOSTS
#-----------------------------------------------------------------------------
def is_ec2_linux():
    """Detect if we are running on an EC2 Linux Instance
        See http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/identify_ec2_instances.html
    """
    if os.path.isfile("/sys/hypervisor/uuid"):
        with open("/sys/hypervisor/uuid") as f:
            uuid = f.read()
            return uuid.startswith("ec2")
    return False

def get_linux_ec2_private_ip():
    """Get the private IP Address of the machine if running on an EC2 linux server"""
    try:
        from urllib2 import urlopen
    except:
        from urllib.request import urlopen
    if not is_ec2_linux():
        return None
    try:
        response = urlopen('http://169.254.169.254/latest/meta-data/local-ipv4')
        return response.read()
    except:
        return None
    finally:
        if response:
           response.close()
#--------------------------------------------------------------------------


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
    '.compute-1.amazonaws.com', # allows viewing of instances directly
    'mitlibraries-hamlet.mit.edu',
    'localhost',
 ]

private_ip = get_linux_ec2_private_ip()
if private_ip:
   ALLOWED_HOSTS.append(private_ip)

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
