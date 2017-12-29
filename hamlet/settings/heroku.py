import dj_database_url
import os
import sys

from .base import *  # noqa


# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)  # noqa


# GENERAL CONFIGURATION
# -----------------------------------------------------------------------------

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = ['mitlibraries-hamlet.herokuapp.com',
                 'mitlibraries-hamlet-staging.herokuapp.com']

# This allows us to include review apps in ALLOWED_HOSTS even though we don't
# know their name until runtime.
APP_NAME = os.environ.get('HEROKU_APP_NAME')
if APP_NAME:
    url = '{}.herokuapp.com'.format(APP_NAME)
    ALLOWED_HOSTS.append(url)

# STATIC FILE CONFIGURATION
# -----------------------------------------------------------------------------

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE += (
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True


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
