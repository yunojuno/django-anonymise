from django.db import models


class GenerateUuid4(models.Func):
    """Run uuid_generate_v4() Postgres function."""

    function = "uuid_generate_v4"
    output_field = models.UUIDField()
    arity = 0

    def as_sqlite(self, compiler, connection, **extra_context):  # type: ignore
        raise NotImplementedError("SQLite does not support native generation of UUIDs.")

    def as_mysql(self, compiler, connection, **extra_context):  # type: ignore
        raise NotImplementedError

    def as_oracle(self, compiler, connection, **extra_context):  # type: ignore
        raise NotImplementedError
