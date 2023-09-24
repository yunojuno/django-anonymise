import logging
import threading
from collections import defaultdict

from django.apps import apps
from django.db import models

from .models import ModelAnonymiser, ModelFieldSummary

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
    return list(_registry.keys())


def anonymisers() -> list[type[ModelAnonymiser]]:
    return list(_registry.values())


def get_model_anonymiser(
    model: type[models.Model],
) -> ModelAnonymiser | None:
    """Return newly instantiated anonymiser for model."""
    if anonymiser := _registry.get(model):
        return anonymiser()
    return None


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
            output[m._meta.label].append(ModelFieldSummary(m, f, anonymiser))
        # sort fields by type then name - easier to scan.
        output[m._meta.label].sort(key=lambda d: f"{d.field_type}.{d.field_name}")
    return dict(output)
