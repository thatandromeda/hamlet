# Sysadmin documentation
This document is for people who are trying to stand up a Hamlet deployment, or understand our existing AWS solution.

## Heroku

We tried to deploy on Heroku but the model file needs ~2GB of memory and that gets spendy. In theory the `hamlet.settings.heroku` file should be deployable with a large enough instance; the app has successfully deployed with small model files (which are too limited to support the app's features). You should be able to use `heroku local` with this file if that is a thing that makes you happy.

## AWS

### Deployment

Hamlet automatically builds to AWS (at https://mitlibraries-hamlet.mit.edu/) via Travis on updates to `master`.
* The build process: see `.ebextensions` files
* Config: `.elasticbeanstalk/config.yml` and `.travis.yml`

### Config

Environment variables defined in AWS for security reasons:
* All Database variables (these are standard and can put directly in your code)
* `SECRET_KEY` - will be created by TS3 or provided by developer securely

All other variables are defined with the config files of the `.ebextensions` folder and can be changed/modified and or added to for future use.

Because the neural net files are too large to live on GitHub, they need to be supplied separately:
* Go to aws.amazon.com
* Make sure you're on US East
* Search for S3
* Find the elasticbeanstalk-us-east-2-214921548711 bucket
* Put model files there

You should be logged in via MIT Touchstone. If you're not in the relevant moira group, ask TS3. Re-uploading files will not trigger a server restart; you'll need to do that manually, or do something to update master and kick off a build.

### Build process
See the scripts in `.ebextensions` for details.

A few rough edges to know about:

Files in the elasticbeanstalk-us-east-2-214921548711 bucket are synced to the build server by the `.ebextensions` scripts. (These are necessary for the app to run but can't be provided via GitHub.) `hamlet.settings.aws` is configured to look for `MODEL_FILE` in the directory created by the build scripts.

AWS doesn't speak Pipfile yet, so we generate `requirements.txt` as part of the deploy process.

### Architecture

The model files live in a bucket on S3. They are expected to change infrequently, so we haven't automated this process; talk to Andy if you need to push changes. The model files are *not* synced through github because they're too large. The s3 bucket is synced to a directory created on the the hamlet instance through a deploy script; `hamlet.settings.aws` creates this directory and tells `MODEL_FILE` to look in it.

Static is deployed using whitenoise within the hamlet instance. It's not big enough for us to have bothered with a real CDN.

Client connections run over https to the load balancer. Connections between the load balancer and the instance(s) are http, but on a private network only accessible by the load balancer and allowed instances. Config is in `.ebextensions/05_elb.config`.

Application logging doesn't actually work right now because the filesystem isn't persistent and we haven't thought through where AWS might want a logstream to go. #yolo
