from .settings import *  # noqa
from os import getenv

import dj_database_url

# this is the default database URL for the docker-compose setup
DEFAULT_DATABASE_URL = "postgres://postgres:postgres@localhost:5432/django_anonymiser"
DATABASE_URL = getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

DATABASES["default"] = dj_database_url.parse(DATABASE_URL)  # noqa: F405
