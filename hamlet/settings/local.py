# This file is designed for use with `heroku local`.
from gensim.models.doc2vec import Doc2Vec
import os

from .heroku import *  # noqa

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1:8000']

SECRET_KEY = 'f=fqwc&$zt_6rf8y45j1l7w!^e*%a_c)4sf+v*_uf%hwf5_*16'

# This should be the full path of the neural net model to be used.
# *Make sure this file is not .gitignored* for Heroku deployment. This means
# it should not live in neural/nets, where the test models are written. Once
# you have selected a test model for use, move it to your preferred location.
MODEL_FILE = os.path.join(PROJECT_DIR, 'model', 'hamlet.model')

NEURAL_NET = Doc2Vec.load(MODEL_FILE)

# The string "PASSED" will pass any captcha.
# Don't use this in production!
# http://django-simple-captcha.readthedocs.io/en/latest/advanced.html#captcha-test-mode
CAPTCHA_TEST_MODE = True
