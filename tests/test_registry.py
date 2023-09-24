from __future__ import annotations

from anonymiser.decorators import register_anonymiser
from anonymiser.registry import (
    ModelFieldSummary,
    _registry,
    anonymisable_models,
)

from .anonymisers import UserAnonymiser
from .models import User


def test_registry() -> None:
    assert anonymisable_models() == [User]


def test_register_anonymiser() -> None:
    _registry.clear()
    assert anonymisable_models() == []
    assert register_anonymiser(UserAnonymiser) == UserAnonymiser
    assert anonymisable_models() == [User]


def test_model_fields_data() -> None:
    mfs = ModelFieldSummary(User._meta.get_field("first_name"))
    assert mfs.app_name == "tests"
    assert mfs.model == User
    assert mfs.model_label == "tests.User"
    assert mfs.field_name == "first_name"
    assert mfs.field_type == "CharField"
    assert isinstance(mfs.anonymiser, UserAnonymiser)
    assert mfs.is_anonymised is True
    assert mfs.is_redacted is True
    assert mfs.redaction_strategy == UserAnonymiser.FieldRedactionStratgy.CUSTOM
