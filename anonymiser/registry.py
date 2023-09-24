import dataclasses
import logging
import threading
from collections import defaultdict

from django.apps import apps
from django.db import models

from .models import ModelAnonymiser

lock = threading.Lock()
logger = logging.getLogger(__name__)


class Registry(dict):
    pass


# global registry
_registry = Registry()


def _register(anonymiser: type[ModelAnonymiser]) -> None:
    if not (model := anonymiser.model):
        raise ValueError("Anonymiser must have a model attribute set.")
    if model in _registry:
        raise ValueError(f"Anonymiser for {model} already registered")
    logging.debug("Adding anonymiser for %s to registry", model._meta.label)
    _registry[model] = anonymiser


def register(anonymiser: type[ModelAnonymiser]) -> None:
    """Add {model: Anonymiser} to the global registry."""
    with lock:
        _register(anonymiser)


def anonymisable_models() -> list[type[models.Model]]:
    with lock:
        return list(_registry.keys())


def not_anonymisable_models() -> list[type[models.Model]]:
    with lock:
        return [m for m in apps.get_models() if m not in _registry]


def anonymisers() -> list[type[ModelAnonymiser]]:
    with lock:
        return list(_registry.values())


def get_model_anonymiser(
    model: type[models.Model],
) -> ModelAnonymiser | None:
    """Return newly instantiated anonymiser for model."""
    with lock:
        if anonymiser := _registry.get(model):
            return anonymiser()
    return None


@dataclasses.dataclass
class ModelFieldSummary:
    """
    Store info about the field and whether it is anonymisable.

    This is used to generate a summary of the fields on a model, and how
    they are anonymised / redacted - used to generate the documentation.

    """

    field: models.Field
    anonymiser: ModelAnonymiser | None = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.anonymiser = get_model_anonymiser(self.model)

    @property
    def model(self) -> type[models.Model]:
        return self.field.model

    @property
    def app_name(self) -> str:
        return self.model._meta.app_label

    @property
    def model_name(self) -> str:
        return self.model._meta.model_name

    @property
    def model_label(self) -> str:
        return self.model._meta.label

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def field_type(self) -> str:
        return self.field.__class__.__name__

    @property
    def is_anonymised(self) -> bool:
        if self.anonymiser:
            return self.anonymiser.is_field_anonymised(self.field)
        return False

    @property
    def is_redacted(self) -> bool:
        if self.anonymiser:
            return self.anonymiser.is_field_redacted(self.field)
        return False

    @property
    def redaction_strategy(self) -> ModelAnonymiser.FieldRedactionStratgy:
        if self.anonymiser:
            return self.anonymiser.field_redaction_strategy(self.field)
        return ModelAnonymiser.FieldRedactionStratgy.NONE


def get_all_model_fields(
    anonymised_only: bool = False,
) -> dict[str, list[ModelFieldSummary]]:
    """
    Return all models and their fields as ModelFieldSummary.

    The return dict uses the `app.Model` string format as the dict key,
    with a list of all fields as the value. This method includes all
    models by default unless the `anonymised_only`
    param is True.

    """
    models = sorted(apps.get_models(), key=lambda m: m._meta.label)
    output = defaultdict(list)
    for m in models:
        anonymiser = get_model_anonymiser(m)
        if anonymised_only and not anonymiser:
            continue
        for f in m._meta.get_fields():
            output[m._meta.label].append(ModelFieldSummary(f))
        # sort fields by type then name - easier to scan.
        output[m._meta.label].sort(key=lambda d: f"{d.field_type}.{d.field_name}")
    return dict(output)
