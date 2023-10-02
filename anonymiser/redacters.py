from __future__ import annotations

from typing import Any, Callable

from django.db import models
from django.utils import timezone

from anonymiser.db.functions import GenerateUuid4


def default_redact_charfield(field: models.CharField) -> str:
    return "X" * field.max_length


def default_redact_textfield(field: models.TextField) -> str:
    return "X" * 400


def default_redact_datefield(field: models.DateField) -> str:
    return timezone.now().date().isoformat()


def default_redact_datetimefield(field: models.DateTimeField) -> str:
    return timezone.now().isoformat()


def default_redact_jsonfield(field: models.JSONField) -> dict[str, Any]:
    return {}


def default_redact_uuidfield(field: models.UUIDField) -> str:
    return GenerateUuid4()


def get_default_field_redacter(
    field: models.Field,
) -> Callable[[models.Field], Any] | None:
    """Return default redacter for basic Django field types."""
    if isinstance(field, models.CharField):
        return default_redact_charfield
    if isinstance(field, models.TextField):
        return default_redact_textfield
    if isinstance(field, models.DateField):
        return default_redact_datefield
    if isinstance(field, models.DateTimeField):
        return default_redact_datetimefield
    if isinstance(field, models.JSONField):
        return default_redact_jsonfield
    if isinstance(field, models.UUIDField):
        return default_redact_uuidfield
    return None
