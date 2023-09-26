from .models import ModelAnonymiser
from .registry import register_model_anonoymiser


def register_anonymiser(anonymiser: type[ModelAnonymiser]) -> type[ModelAnonymiser]:
    """Add {model: Anonymiser} to the global registry."""
    register_model_anonoymiser(anonymiser)
    return anonymiser
