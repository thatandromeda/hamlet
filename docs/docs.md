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
