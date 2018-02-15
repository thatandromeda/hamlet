from gensim.models.doc2vec import Doc2Vec
import os

from .base import *

# This is a model designed to:
#   * be small enough that we don't have to .gitignore it
#   * contain everything we need to run the tests
MODEL_FILE = os.path.join(PROJECT_DIR, 'testmodels', 'testmodel.model')

NEURAL_NET = Doc2Vec.load(MODEL_FILE)
CAPTCHA_TEST_MODE = True
