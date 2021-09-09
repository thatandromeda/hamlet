FROM python:3.8

RUN python3.8 -m pip install pipenv

COPY hamlet/ /hamlet/hamlet/
COPY Pipfile* /hamlet/
COPY manage.py /hamlet/
COPY entrypoint.sh /hamlet/
WORKDIR /hamlet
RUN pipenv install --system --deploy

ENV DJANGO_SETTINGS_MODULE "hamlet.settings.docker"

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
