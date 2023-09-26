from __future__ import annotations

from anonymiser.decorators import register_anonymiser
from anonymiser.registry import _registry

from .anonymisers import UserAnonymiser
from .models import User


def test_registry() -> None:
    assert list(_registry.keys()) == [User]


def test_register_anonymiser() -> None:
    _registry.clear()
    assert _registry == {}
    register_anonymiser(UserAnonymiser)
    assert _registry == {User: UserAnonymiser}
