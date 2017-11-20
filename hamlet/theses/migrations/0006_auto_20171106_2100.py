# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-06 21:00
from __future__ import unicode_literals
import os
import pickle

from gensim.models.doc2vec import Doc2Vec

from django.conf import settings
from django.db import migrations

from hamlet.neural.train_neural_net import LabeledLineSentence


def add_vector_data(apps, schema_editor):
    # Set up needed context.
    lls = LabeledLineSentence('fake')
    files_dir = os.path.join(settings.PROJECT_DIR, 'neural', 'files', 'main')
    model_file = os.path.join(settings.PROJECT_DIR, 'neural', 'hamlet.model')
    model = Doc2Vec.load(model_file)
    Thesis = apps.get_model('theses', 'Thesis')

    # Generate and save inferred vector for each thesis.
    for thesis in Thesis.objects.filter(unextractable=False):
        print('Generating vector for {}'.format(thesis.identifier))
        fn = os.path.join(files_dir, '1721.1-{}.txt'.format(thesis.identifier))
        with open(fn, 'r') as f:
            doc = f.read()

        print('Tokenizing')
        tokens = lls._tokenize(doc)
        print('Inferring vector')
        vector = model.infer_vector(tokens)
        print(vector)
        print('Pickling vector')
        foo = pickle.dumps(vector)
        print(foo)
        thesis._vector = foo
        print('Saving thesis')
        thesis.save()


def remove_vector_data(apps, schema_editor):
    Thesis = apps.get_model('theses', 'Thesis')
    Thesis.objects.filter(unextractable=False).update(_vector=None)


class Migration(migrations.Migration):

    dependencies = [
        ('theses', '0005_thesis__vector'),
    ]

    operations = [
        migrations.RunPython(add_vector_data, remove_vector_data),
    ]
