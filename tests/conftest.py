import pytest
from django.conf import settings

from tests.anonymisers import UserAnonymiser, UserRedacter
from tests.models import User

IS_POSTGRES = (
    not settings.DATABASES["default"]["ENGINE"].endswith("postgresql"),
    "PostgreSQL only",
)


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        username="testuser1",
        first_name="fred",
        last_name="flintstone",
        location="London",
        biography="I am a test user",
    )


@pytest.fixture
def user2() -> User:
    return User.objects.create_user(
        username="testuser2",
        first_name="ginger",
        last_name="rogers",
        location="New York",
        biography="I am another test user",
    )


@pytest.fixture
def user_anonymiser() -> UserAnonymiser:
    return UserAnonymiser()


@pytest.fixture
def user_redacter() -> UserRedacter:
    return UserRedacter()
