from .models import AnonymiserBase, RedacterBase
from .registry import register


def register_anonymiser(
    anonymiser: type[AnonymiserBase | RedacterBase],
) -> type[AnonymiserBase | RedacterBase]:
    """Add {model: Anonymiser} to the global registry."""
    register(anonymiser)
    return anonymiser
