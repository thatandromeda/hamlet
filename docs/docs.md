# Documentation

## Systems

Running with pipenv. There's a .env file (kept out of version control) for use by `pipenv shell`. It specifies:
DJANGO_SETTINGS_MODULE='hamlet.settings.local' # for using heroku local
or DJANGO_SETTINGS_MODULE='hamlet.settings.base' # for python manage.py runserver
DJANGO_DB_PASSWORD='(your password)'
DJANGO_DEBUG_IS_TRUE='True' (if you want)
DSPACE_OAI_IDENTIFIER
DSPACE_OAI_URI

tika requires Java, so probably we want to preprocess PDFs off of Heroku.

nltk might require stuff?

gensim wants a C compiler.

Postgres needs a database and user (default values are 'hamlet' for database name and username, no password; override this if desired in .env with DJANGO_DB, DJANGO_DB_USER, DJANGO_DB_PASSWORD)

## Static assets
If you need to edit styles, edit files in `hamlet/static/sass/apps/`. Don't edit css directly - these changes will be blown away during asset precompilation.

### for `python manage.py runserver`
* run `python manage.py collectstatic`
* use `hamlet.settings.base`

### for `heroku local`
* run `python manage.py compress`
* then run `python manage.py collectstatic`
* use `hamlet.settings.local`

## The neural net
hamlet.model is a copy of max_250k_truncated.model. This is a model trained with a window size of 4 and a step of 52, limited to a vocabulary of 250k words, and saved with temporary training data deleted (but doctags vectors and inferences kept).

## Heroku

## AWS
