# Documentation
This document is for people who are trying to stand up an instance of Hamlet on localhost in order to write code. It assumes you are generally familiar with setting up development environments (for instance, that you can install Python dependencies and stand up local Postgres).

## Tests
Run tests with `python manage.py test --settings=hamlet.settings.test`.

This ensures that they use the test neural net. The primary keys of objects in
the test file are written around the assumption that they will be present in
both the test net and the fixtures.

You can generate additional fixtures with statements like `python manage.py dumpdata theses.Person --pks=63970,29903 > hamlet/theses/fixtures/authors.json`, but make sure to include the pks of all objects already in the fixtures (or to write it to a separate file and then unite it with the existing - you can't just append because the json syntax will be wrong). Also make sure that the theses you use are in fact present in the test neural net.

### Checking that a document is in a given neural net

* Make sure your settings file points to the desired `MODEL_FILE`
* `python manage.py shell`

```
from gensim.models.doc2vec import Doc2Vec
from django.conf import settings
model = Doc2Vec.load(settings.MODEL_FILE)
identifier = '1721.1-%d.txt' % YOUR THESIS IDENTIFIER HERE
identifier in model.docvecs.doctags.keys()
```

If you don't have a target thesis object but you need one you know is in the neural net, look at the output of `model.docvecs.doctags.keys()`. This is a list of filenames of text files from dspace; they are all of the format `1721.1-NUMBER.txt`, where `NUMBER` is the identifier of the thesis. You can look up `Thesis` objects in your database by this identifier (which is `Thesis.identifier`, not the primary key).

## System configuration

### Development dependencies: pipenv
For the most part, dependencies are installed via pipenv. There's a `.env` file (kept out of version control) for use by `pipenv shell`. It specifies:
* `DJANGO_SETTINGS_MODULE`
  * `DJANGO_SETTINGS_MODULE='hamlet.settings.local'` (for using heroku local)
  * `DJANGO_SETTINGS_MODULE='hamlet.settings.base'` (for python manage.py runserver)
* `DJANGO_DB_PASSWORD='(your password)'`
* `DJANGO_DEBUG_IS_TRUE='True' (if you want)`
* `DSPACE_OAI_IDENTIFIER`
* `DSPACE_OAI_URI`

The latter two are only relevant if you plan to be downloading files or metadata from DSpace. They can be omitted or given dummy values otherwise.

### Additional non-pipenv dependencies
Some dependencies require extra help:
* tika requires Java
* nltk may require installing corpora through the python shell
* gensim wants a C compiler (it can run without one but will be 70x slower; a single neural net training run can take literally days in this case)
* python-magic needs libmagic (`brew install libmagic` on OSX).
* captcha says it needs `apt-get -y install libz-dev libjpeg-dev libfreetype6-dev python-dev` or similar. You can't yum install them on AWS, but the captcha works anyway, so maybe it's lying.

You only need the first three of these if you plan to be doing neural net training. If you're developing the Django parts you can skip them; just get a prebuilt neural net file (see below, "Neural net files").

### Other config
You may set the following environment variables to configure your database:
* `DJANGO_DB_ENGINE` (default `django.db.backends.postgresql`)
* `DJANGO_DB` (default `hamlet`)
* `DJANGO_DB_USER` (default `hamlet`)
* `DJANGO_DB_PASSWORD` (no default)
* `DJANGO_DB_HOST` (default `localhost`)

If you are running with the Postgres default, be sure to stand up Postgres; create the named database and user; and grant privileges on your database to your user.

## Static assets
If you need to edit styles, edit files in `hamlet/static/sass/apps/`. Don't edit css directly - these changes will be blown away during asset precompilation.

### for `python manage.py runserver`
* run `python manage.py collectstatic`
* use `hamlet.settings.base`

### for `heroku local`
* run `python manage.py compress`
* then run `python manage.py collectstatic`
* use `hamlet.settings.local`

### for AWS
The static asset pipeline runs automatically; see `.ebextensions/02_python.config`.

## Neural net files
hamlet.model is a copy of all_theses_no_split_w4_s52.model. This is a model trained with a window size of 4 and a step of 52. It is kept out of version control because it is too big.

`hamlet/testmodels/` contains some smaller models not suitable for production, but usable for testing (and small enough to be pushed to GitHub, although it will complain, and hence used on Travis). You can configure your local settings to point at these files and that will suffice for development.

These models don't represent the entire MIT thesis collection (that's what lets them be smaller), so don't be surprised if documents of interest are not present.

`hamlet.settings.local` defaults to using the test model, since it is checked
into version control. If you have a different model you want to use, set `DJANGO_MODEL_PATH=/full/path/to/model` in `.env`.

## Docker
You can start up a running instance locally using docker compose:

```
$ docker-compose up
```

By default, this will use the test model included in the codebase. If you'd like to use a different model, you will need to add it to a hamlet docker volume. This volume is mounted as `/data` in the container. You'll also need to set the `DJANGO_MODEL_PATH` env var to point to the model within that docker volume. Assuming your model files are in the top directory of the project:

```
$ docker run --name hamlet-data --mount type=volume,src=hamlet,target=/data busybox true
$ for f in hamlet.model*; do docker cp $f hamlet-data:/data; done
$ docker rm hamlet-data
$ export DJANGO_MODEL_PATH=/data/hamlet.model
$ docker-compose up
```
