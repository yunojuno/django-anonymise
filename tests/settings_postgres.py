from tests.settings import *  # noqa
from os import getenv

import dj_database_url

DEFAULT_DATABASE_URL = getenv(
    "DATABASE_URL", "postgres://postgres@localhost:5432/django_anonymiser"
)
DATABASES["default"] = dj_database_url.parse(DEFAULT_DATABASE_URL)  # noqa: F405
