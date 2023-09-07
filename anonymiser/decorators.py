from .models import BaseAnonymiser
from .registry import register


def register_anonymiser(anonymiser: type[BaseAnonymiser]) -> type[BaseAnonymiser]:
    """Add {model: Anonymiser} to the global registry."""
    register(anonymiser)
    return anonymiser
