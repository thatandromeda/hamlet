"""
Django settings for hamlet project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)


# -----------------------------------------------------------------------------
# ------------------------> core django configurations <-----------------------
# -----------------------------------------------------------------------------

# APP CONFIGURATION
# -----------------------------------------------------------------------------

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

HAMLET_APPS = [
    'hamlet.theses',
]

THIRD_PARTY_APPS = [
    'dal',
    'dal_select2',
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + HAMLET_APPS


# MIDDLEWARE CONFIGURATION
# -----------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# DEBUG
# -----------------------------------------------------------------------------

# Set DJANGO_DEBUG_IS_TRUE to anything on servers if you want DEBUG to be true.
# Unset if you want DEBUG=False. This makes it easy to flip settings on test
# servers.
# SECURITY WARNING: don't run with debug turned on in production!

PROTO_DEBUG = os.environ.get('DJANGO_DEBUG_IS_TRUE', True)

if 'DJANGO_DEBUG_IS_TRUE' in os.environ:
    DEBUG = True
else:
    DEBUG = False


# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE',
                                 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DJANGO_DB', 'hamlet'),
        'USER': os.environ.get('DJANGO_DB_USER', 'hamlet'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD'),
        'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
        'PORT': '',
    }
}


# GENERAL CONFIGURATION
# -----------------------------------------------------------------------------

# SECURITY WARNING: keep the secret key used in production secret!
# This should only be used for local development.
SECRET_KEY = 'f=fqwc&$zt_6rf8y45j1l7w!^e*%a_c)4sf+v*_uf%hwf5_*16'

# This is not usable in production. Prod files should list the actually
# allowed hosts.
ALLOWED_HOSTS = ['localhost', '0.0.0.0', '127.0.0.1', '127.0.0.1:8000']

ROOT_URLCONF = 'hamlet.urls'

WSGI_APPLICATION = 'hamlet.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]


# INTERNATIONALIZATION CONFIGURATION
# -----------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = False

USE_TZ = True


# TEMPLATE CONFIGURATION
# -----------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# STATIC FILE CONFIGURATION
# -----------------------------------------------------------------------------

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'hamlet', 'static'),
)

FIXTURE_DIRS = [os.path.join(BASE_DIR, 'hamlet', 'fixtures')]


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
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'hamlet.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'brief',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
        }
    }
}


# -----------------------------------------------------------------------------
# -----------------> third-party and hamlet configurations <-----------------
# -----------------------------------------------------------------------------

# DJANGO-COMPRESSOR CONFIGURATION
# -----------------------------------------------------------------------------

INSTALLED_APPS += ('compressor',)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False  # The default, but we're being explicit.

COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'django_libsass.SassCompiler'),
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

COMPRESS_ROOT = STATIC_ROOT

# DJANGO-SIMPLE-CAPTCHA CONFIGURATION
# -----------------------------------------------------------------------------

INSTALLED_APPS += ('captcha',)


# DJANGO-HEALTH-CHECK CONFIGURATION
# -----------------------------------------------------------------------------

INSTALLED_APPS += (
    'health_check',                             # required
    'health_check.db',                          # stock Django health checkers
    'health_check.cache',
    'health_check.storage',
)
