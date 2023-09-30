from __future__ import annotations

from typing import Any, Callable

from django.conf import settings as django_settings
from django.db import models
from django.utils import timezone

from .db.functions import GenerateUuid4


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


AUTO_REDACT_FIELD_FUNCS: dict[
    type[models.Model],
    Callable[[type[models.Field]], Any],
] = {
    models.CharField: default_redact_charfield,
    models.TextField: default_redact_textfield,
    models.DateField: default_redact_datefield,
    models.DateTimeField: default_redact_datetimefield,
    models.JSONField: default_redact_jsonfield,
    models.UUIDField: default_redact_uuidfield,
}

# update map with any new field types or overrides declared in settings
AUTO_REDACT_FIELD_FUNCS.update(
    getattr(django_settings, "ANONYMISER_AUTO_REDACT_FIELD_FUNCS", {})
)
