import logging
import threading

from django.db import models

from .models import AnonymiserBase, RedacterBase

lock = threading.Lock()
logger = logging.getLogger(__name__)


class Registry(dict):
    pass


# global registry
_registry = Registry()


def _register(anonymiser: type[AnonymiserBase | RedacterBase]) -> None:
    if not (model := anonymiser.model):
        raise ValueError("Anonymiser must have a model attribute set.")
    if model in _registry:
        raise ValueError(f"Anonymiser for {model} already registered")
    logging.debug("Adding anonymiser for %s to registry", model._meta.label)
    _registry[model] = anonymiser


def register(anonymiser: type[AnonymiserBase | RedacterBase]) -> None:
    """Add {model: Anonymiser} to the global registry."""
    with lock:
        _register(anonymiser)


def anonymisable_models() -> list[type[models.Model]]:
    return list(_registry.keys())


def anonymisers() -> list[type[AnonymiserBase | RedacterBase]]:
    return list(_registry.values())


def get_model_anonymiser(
    model: type[models.Model],
) -> AnonymiserBase | RedacterBase | None:
    """Return newly instantiated anonymiser for model."""
    if anonymiser := _registry.get(model):
        return anonymiser()
    return None
