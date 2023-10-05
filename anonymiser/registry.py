from __future__ import annotations

import logging
import threading
from collections import defaultdict

from django.apps import apps
from django.db import models

from .models import ModelAnonymiser, ModelFieldSummary

lock = threading.Lock()
logger = logging.getLogger(__name__)


def sort_by_name(models: list[type[models.Model]]) -> list[type[models.Model]]:
    return sorted(models, key=lambda m: m._meta.label)


class Registry(dict):
    def get_anonymisable_models(self) -> list[type[models.Model]]:
        return sort_by_name([m for m in self.keys() if self[m]])

    def is_model_anonymisable(self, model: type[models.Model]) -> bool:
        return bool(self[model])

    def register_anonymiser(self, anonymiser: type[ModelAnonymiser]) -> None:
        with lock:
            if not (model := anonymiser.model):
                raise ValueError("Anonymiser must have a model attribute set.")
            if model in self:
                raise ValueError(f"Anonymiser for {model} already registered")
            logging.debug("Adding anonymiser for %s to registry", model._meta.label)
            self[model] = anonymiser


def register_model_anonymiser(anonymiser: type[ModelAnonymiser]) -> None:
    _registry.register_anonymiser(anonymiser)


def get_model_anonymiser(model: type[models.Model]) -> ModelAnonymiser | None:
    """Return newly instantiated anonymiser for model."""
    if anonymiser := _registry.get(model):
        return anonymiser()
    return None


def get_anonymisable_models() -> list[type[models.Model]]:
    """Return all models that have an anonymiser."""
    return _registry.get_anonymisable_models()


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


# principle access point for the registry
_registry = Registry()
