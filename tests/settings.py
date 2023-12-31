from os import getenv, path

import dj_database_url

DEBUG = True
TEMPLATE_DEBUG = True
USE_TZ = True

DATABASE_URL = getenv("DATABASE_URL", "sqlite:///django_anonymise.db")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
# used to skip non-PG tests
IS_SQLITE = DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
IS_POSTGRES = DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "anonymiser",
    "tests",
)

MIDDLEWARE = [
    # default django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

PROJECT_DIR = path.abspath(path.join(path.dirname(__file__)))

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path.join(PROJECT_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
            ]
        },
    }
]

STATIC_URL = "/static/"

SECRET_KEY = "secret"  # noqa: S105

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(message)s"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "loggers": {
        "": {"handlers": ["console"], "propagate": True, "level": "DEBUG"},
        # 'django': {
        #     'handlers': ['console'],
        #     'propagate': True,
        #     'level': 'WARNING',
        # },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

ROOT_URLCONF = "tests.urls"

# silence warning models.W042
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

if not DEBUG:
    raise Exception("This settings file can only be used with DEBUG=True")

AUTH_USER_MODEL = "tests.User"
