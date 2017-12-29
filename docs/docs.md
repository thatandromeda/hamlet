# Documentation

Run tests with `python manage.py test --settings=hamlet.settings.test`.

This ensures that they use the test neural net. The primary keys of objects in
the test file are written around the assumption that they will be present in
both the test net and the fixtures.

You can generate additional fixtures with statements like `python manage.py dumpdata theses.Person --pks=63970,29903 > hamlet/theses/fixtures/authors.json`, but make sure to include the pks of all objects already in the fixtures (or to write it to a separate file and then unite it with the existing - you can't just append because the json syntax will be wrong).

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

python-magic needs libmagic (`brew install libmagic` on OSX).

captcha needs `apt-get -y install libz-dev libjpeg-dev libfreetype6-dev python-dev` or similar.

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
hamlet.model is a copy of all_theses_no_split_w4_s52.model. This is a model trained with a window size of 4 and a step of 52. It is kept out of version control because it is too big.

`hamlet/testmodels/` contains some smaller models not suitable for production, but usable for testing (and small enough to be pushed to GitHub, although it will complain, and hence used on Travis).

## Heroku

We tried to deploy on Heroku but the model file needs ~2GB of memory and that gets spendy. In theory the `hamlet.settings.heroku` file should be deployable with a large enough instance; the app has successfully deployed with small model files (which are too limited to support the app's features).

## AWS

https://mitlibraries-hamlet.mit.edu/

Environment Varibles defined in AWS for security reasons:
-All Database variables (these are standard and can put directly in your code)
-SECRET_KEY - will be created by TS3 or provided by developer securely

All other variables are defined with the config files of the .ebextensions folder and can be changed/modified and or added to for future use.

aws.amazon.com -
* search for S3
* find the hamlet-models bucket
* put model files there

You should be logged in via MIT Touchstone. If you're not in the relevant moira group, ask TS3. Re-uploading files will not trigger a server restart; you'll need to do that manually, or do something to update master and kick off a build.

### Deployment

The goal is to have master autodeploy via Travis. Right now if you want something to be deployed, ask Andy.

AWS doesn't speak Pipfile yet, so we generate requirements.txt as part of the deploy process.

### Architecture

The model files live in a bucket on S3. They are expected to change infrequently, so we haven't automated this process; talk to Andy if you need to push changes. The model files are *not* synced through github because they're too large. The s3 bucket is synced to a directory created on the the hamlet instance through a deploy script; `hamlet.settings.aws` creates this directory and tells `MODEL_FILE` to look in it.

Static is deployed using whitenoise within the hamlet instance. It's not big enough for us to have bothered with a real CDN.

Client connections run over https to the load balancer. Connections between the load balancer and the instance(s) are http, but on a private network only accessible by the load balancer and allowed instances. Config is in `.ebextensions/05_elb.config`.

Application lgging doesn't actually work right now because the filesystem isn't persistent and we havne't thought through where AWS might want a logstream to go. #yolo
