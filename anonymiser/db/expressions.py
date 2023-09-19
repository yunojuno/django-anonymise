from typing import Any

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.sql.compiler import SQLCompiler

# sql methods return a tuple of (sql, params)
EXPR_RETURN_TYPE = tuple[str, list]


class GenerateUuid4(models.Func):
    """Run uuid_generate_v4() Postgres function."""

    output_field = models.UUIDField()

    def as_sql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        **extra_context: Any,
    ) -> EXPR_RETURN_TYPE:
        if connection.vendor in ("sqlite", "postgresql"):
            return super().as_sql(compiler, connection, **extra_context)
        raise NotImplementedError(
            f"GenerateUuid4 is not implemented for {connection.vendor}"
        )

    def as_sqlite(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        **extra_context: Any,
    ) -> EXPR_RETURN_TYPE:
        return "HEX(RANDOMBLOB(16))", []

    def as_postgresql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        **extra_context: Any,
    ) -> EXPR_RETURN_TYPE:
        return "get_random_uuid()", []
