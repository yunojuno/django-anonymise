from unittest import mock, skipIf

import pytest
from django.conf import settings
from django.db.backends.utils import CursorWrapper

from anonymiser.db.expressions import GenerateUuid4

from .models import User

# skip if we're using SQLite as it doesn't support UUIDs
is_sqlite = settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"


@skipIf(is_sqlite, "SQLite does not support native generation of UUIDs.")
@pytest.mark.django_db
@mock.patch.object(CursorWrapper, "execute")
def test_generate_uuid4(mock_execute: mock.MagicMock) -> None:
    User.objects.update(uuid=GenerateUuid4())
    assert (
        mock_execute.call_args[0][0]
        == 'UPDATE "tests_user" SET "uuid" = uuid_generate_v4()'
    )
