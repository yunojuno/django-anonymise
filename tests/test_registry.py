from anonymiser.decorators import register_anonymiser
from anonymiser.registry import _registry, anonymisable_models

from .anon import UserAnonymiser
from .models import User


def test_registry() -> None:
    # assert anonymisable_models() == []
    # register(UserAnonymiser)
    assert anonymisable_models() == [User]


def test_register_anonymiser() -> None:
    _registry.clear()
    assert anonymisable_models() == []
    assert register_anonymiser(UserAnonymiser) == UserAnonymiser
    assert anonymisable_models() == [User]
