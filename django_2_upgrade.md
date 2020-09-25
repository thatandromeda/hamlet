# IN PROGRESS

# TO DO

# OPTIONAL
- migrate raven (it's deprecated) to https://github.com/getsentry/sentry-python
- figure out fail2ban or something because all your traffic is people probing for vulns
- update AWS environment
    - note that this moves from apache to nginx
- update postgres
    - you're on 9.6.11
    - latest is 13 (!) (but they changed the policy I think so major numbers change much faster)
    - 9.6 is supported through November 2021 (!) but it's up to 9.6.19

# DONE
- run tests under 1.11 and fix deprecation warnings (`python -Wa manage.py test --settings=hamlet.settings.test`)
- check each of these: https://eldarion.com/blog/2017/12/26/10-tips-upgrading-django-20/
- update to best available version of deps before updating django
- upgrade to django 2.0
- use updated URL routing syntax
- look for `from django.conf.urls import include` and update to `from django.urls import include`
- check to see if I have a model inheriting from AbstractUser https://docs.djangoproject.com/en/3.1/releases/2.0/#abstractuser-last-name-max-length-increased-to-150
- see if I use QuerySet.reverse() or .last() https://docs.djangoproject.com/en/3.1/releases/2.0/#queryset-reverse-and-last-are-prohibited-after-slicing
- remove `SessionAuthenticationMiddleware` if used
- update syntax for `handler404` and other handlers
- see if I use `RedirectView` and need to handle `NoReverseMatch` exceptions
- run tests under 2.0 and fix deprecation warnings
- then stepwise to 2.1
- check postgres version on AWS
    - 2.1 dropped support for < 9.4
    - it's pg 9.6 so we're all good
- backup db before deploy
- check deploy script for migration-running
- then stepwise to 2.2
    + 2.2 is LTS so I can stay here.
    + 3.1 is latest stable, but 3 won't be LTS until 3.2 in 2021, so I SHOULD stay on 2.2.
    + current issue: things aren't in the static manifest. base settings works, local does not, aws is different and might work??

