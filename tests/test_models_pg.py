from unittest import SkipTest, mock

import pytest
from django.conf import settings
from django.db import connection
from django.db.backends.utils import CursorWrapper

from anonymiser.db.expressions import GenerateUuid4

from .anon import UserAnonymiser
from .models import User

# skip if we're using SQLite as it doesn't support UUIDs
if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # this will skip all tests in this file
    raise SkipTest("Skipping Postgres tets as SQLite is being used.")


@pytest.mark.django_db
@mock.patch.object(CursorWrapper, "execute")
def test_generate_uuid4(mock_execute: mock.MagicMock) -> None:
    User.objects.update(uuid=GenerateUuid4())
    assert (
        mock_execute.call_args[0][0]
        == 'UPDATE "tests_user" SET "uuid" = uuid_generate_v4()'
    )


@pytest.mark.django_db
class TestPostgresRedaction:
    @pytest.fixture(autouse=True)
    def activate_postgresql_uuid(self) -> None:
        """Activate the uuid-ossp extension in the test database."""
        with connection.cursor() as cursor:
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    def test_redact_queryset_none(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        assert user_anonymiser.redact_queryset(User.objects.none()) == 0

    def test_redact_queryset_one(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        uuid = user.uuid
        assert user_anonymiser.redact_queryset(User.objects.all()) == 1
        user.refresh_from_db()
        assert user.first_name == "FIRST_NAME"
        assert user.last_name == "LAST_NAME"
        assert user.uuid != uuid

    def test_redact_queryset_two(
        self,
        user: User,
        user2: User,
        user_anonymiser: UserAnonymiser,
    ) -> None:
        assert user_anonymiser.redact_queryset(User.objects.all()) == 2
        user.refresh_from_db()
        user2.refresh_from_db()
        # confirm that we haven't reused the same uuid for all objects
        assert user.uuid != user2.uuid

    @pytest.mark.parametrize(
        "auto_redact,location,biography",
        [
            (True, 255 * "X", 400 * "X"),
            (False, "London", "I am a test user"),
        ],
    )
    def test_redact_queryset__auto_redact(
        self,
        user: User,
        user_anonymiser: UserAnonymiser,
        auto_redact: bool,
        location: str,
        biography: str,
    ) -> None:
        user_anonymiser.redact_queryset(User.objects.all(), auto_redact=auto_redact)
        user.refresh_from_db()
        # auto-redacted fields
        assert user.location == location
        assert user.biography == biography

    def test_redact_queryset__field_overrides(
        self,
        user: User,
        user_anonymiser: UserAnonymiser,
    ) -> None:
        user_anonymiser.redact_queryset(User.objects.all(), location="Area 51")
        user.refresh_from_db()
        # auto-redacted fields
        assert user.location == "Area 51"
