from gensim.models.doc2vec import Doc2Vec
import os

from .local import *  # noqa

# This should be the full path of the neural net model to be used.
# *Make sure this file is not .gitignored* for Heroku deployment. This means
# it should not live in neural/nets, where the test models are written. Once
# you have selected a test model for use, move it to your preferred location.
MODEL_FILE = os.path.join(PROJECT_DIR, 'testmodels', 'testmodel.model')

NEURAL_NET = Doc2Vec.load(MODEL_FILE)
