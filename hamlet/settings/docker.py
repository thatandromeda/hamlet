# This file is designed for use with docker.
from gensim.models.doc2vec import Doc2Vec
import os

from .base import *  # noqa

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'localhost']

SECRET_KEY = 'f=fqwc&$zt_6rf8y45j1l7w!^e*%a_c)4sf+v*_uf%hwf5_*16'

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MODEL_FILE is the full path of the neural net model to be used.
# *Make sure the test file is not .gitignored*; it is needed for CI.
# However, production-quality models are too big for GitHub, so they should be
# .gitignored.
# MODEL_FILE defaults to the test model used for CI; because it is checked into
# the repo it should be present and is therefore a sensible default for local
# development. If you want to have a production-like environment, and to use
# a model that represents the entire database, get it separately; set the
# env var DJANGO_MODEL_PATH to the full path to the neural net model.
MODEL_FILE = os.environ.get('DJANGO_MODEL_PATH',
                            os.path.join(PROJECT_DIR, 'testmodels', 'testmodel.model'))
NEURAL_NET = Doc2Vec.load(MODEL_FILE)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARN'),
        },
    },
}
