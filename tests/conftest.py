import pytest
from django.conf import settings

from tests.anon import UserAnonymiser
from tests.models import User

IS_POSTGRES = (
    not settings.DATABASES["default"]["ENGINE"].endswith("postgresql"),
    "PostgreSQL only",
)


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        username="testuser1", first_name="fred", last_name="flintstone"
    )


@pytest.fixture
def user2() -> User:
    return User.objects.create_user(
        username="testuser2", first_name="ginger", last_name="rogers"
    )


@pytest.fixture
def user_anonymiser() -> UserAnonymiser:
    return UserAnonymiser()
