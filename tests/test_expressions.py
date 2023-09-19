from unittest import mock

import pytest
from django.db import connection
from django.db.backends.utils import CursorWrapper

from anonymiser.db.functions import GenerateUuid4

from .models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "vendor,sql_func",
    [
        ("sqlite", "HEX(RANDOMBLOB(16))"),
        ("postgresql", "gen_random_uuid()"),
    ],
)
@mock.patch.object(CursorWrapper, "execute")
def test_generate_uuid4(
    mock_execute: mock.MagicMock, vendor: str, sql_func: str
) -> None:
    uuid_expression = GenerateUuid4()
    with mock.patch.object(connection, "vendor", vendor):
        assert connection.vendor == vendor
        User.objects.update(uuid=uuid_expression)
        assert mock_execute.call_args[0][0] == (
            f'UPDATE "tests_user" SET "uuid" = {sql_func}'  # noqa: S608
        )


@pytest.mark.django_db
@pytest.mark.parametrize("vendor", ["mysql", "oracle"])
def test_unsupported_databases_engines(vendor: str) -> None:
    uuid_expression = GenerateUuid4()
    with mock.patch.object(connection, "vendor", vendor):
        assert connection.vendor == vendor
        with pytest.raises(NotImplementedError):
            uuid_expression.as_sql(None, connection)
