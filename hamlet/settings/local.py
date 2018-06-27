# This file is designed for use with `heroku local`.
from gensim.models.doc2vec import Doc2Vec
import os

from .heroku import *  # noqa

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1']

SECRET_KEY = 'f=fqwc&$zt_6rf8y45j1l7w!^e*%a_c)4sf+v*_uf%hwf5_*16'

# MODEL_FILE is the full path of the neural net model to be used.
# *Make sure the test file is not .gitignored*; it is needed for CI.
# However, production-quality models are too big for GitHub, so they should be
# .gitignored.
# MODEL_FILE defaults to the test model used for CI; because it is checked into
# the repo it should be present and is therefore a sensible default for local
# development. If you want to have a production-like environment, and to use
# a model that represents the entire database, get it separately; put it in
# hamlet/model/hamlet.model; and add DJANGO_USE_LIVE_MODEL=True to your .env.
modelpath = os.environ.get('DJANGO_MODEL_PATH', '')
if modelpath:
    MODEL_FILE = os.path.join(PROJECT_DIR, modelpath)
else:
    MODEL_FILE = os.path.join(PROJECT_DIR, 'testmodels', 'testmodel.model')

NEURAL_NET = Doc2Vec.load(MODEL_FILE)

# The string "PASSED" will pass any captcha.
# Don't use this in production!
# http://django-simple-captcha.readthedocs.io/en/latest/advanced.html#captcha-test-mode
CAPTCHA_TEST_MODE = True
