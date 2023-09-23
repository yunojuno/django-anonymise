from .models import ModelAnonymiser
from .registry import register


def register_anonymiser(
    anonymiser: type[ModelAnonymiser],
) -> type[ModelAnonymiser]:
    """Add {model: Anonymiser} to the global registry."""
    register(anonymiser)
    return anonymiser
