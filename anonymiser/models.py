from __future__ import annotations

import dataclasses
import logging
from enum import StrEnum  # 3.11 only
from typing import Any, Callable, TypeAlias

from django.db import models

from .redacters import get_default_field_redacter

# (old_value, new_value) tuple
AnonymisationResult: TypeAlias = tuple[Any, Any]

logger = logging.getLogger(__name__)


def get_model_fields(model: type[models.Model]) -> list[models.Field]:
    """
    Return a list of fields on the model.

    Removes any related_name fields.

    """
    return [
        f
        for f in model._meta.get_fields()
        if not isinstance(f, models.ForeignObjectRel)
    ]


class _ModelBase:
    # Override with the model to be anonymised
    model: type[models.Model]

    def get_model_fields(self) -> list[models.Field]:
        """Return a list of fields on the model."""
        if not self.model:
            raise NotImplementedError("model must be set")
        return get_model_fields(self.model)


class AnonymiserBase(_ModelBase):
    """Base class for anonymisation functions."""

    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        Prevent setting of attribute on the anonymiser itself.

        This is a common mistake when writing anonymiser functions -
        inside the `anonymise_FOO` method you call `self.FOO = "bar"`
        instead of `obj.FOO = "bar"`, because that's the natural way to
        write it.

        This will raise an AttributeError if you try to set an attribute
        that looks like it maps to an anonymiser method.

        """
        if hasattr(self, f"anonymise_{__name}"):
            raise AttributeError(
                "Cannot set anonymiser attributes directly - did you mean to "
                "use 'obj' instead of 'self' in method "
                f"`{self.__class__.__name__}.anonymise_{__name}`?"
            )
        super().__setattr__(__name, __value)

    def is_field_anonymised(self, field: models.Field) -> bool:
        return hasattr(self, f"anonymise_{field.name}")

    def get_anonymisable_fields(self) -> list[models.Field]:
        """Return a list of fields on the model that are anonymisable."""
        return [f for f in self.get_model_fields() if self.is_field_anonymised(f)]

    def anonymise_field(
        self, obj: models.Model, field: models.Field
    ) -> AnonymisationResult:
        """Anonymise a single field on the model instance."""
        field_name = field.name
        if not (anon_func := getattr(self, f"anonymise_{field_name}", None)):
            raise NotImplementedError(
                f"Anonymiser function 'anonymise_{field_name}' not implemented"
            )
        old_value = getattr(obj, field_name)
        anon_func(obj)
        new_value = getattr(obj, field_name)
        return old_value, new_value

    def anonymise_object(self, obj: models.Model) -> None:
        """Anonymise the model instance (NOT THREAD SAFE)."""
        output = {}
        for field in self.get_anonymisable_fields():
            output[field.name] = self.anonymise_field(obj, field)
        self.post_anonymise_object(obj, **output)

    def post_anonymise_object(
        self, obj: models.Model, **updates: AnonymisationResult
    ) -> None:
        """
        Post-process the model instance after anonymisation.

        The updates param is a dict of field names to (old_value, new_value) tuples.

        """
        pass


class RedacterBase(_ModelBase):
    """Base class for redaction functions."""

    # Set to False to disable auto-redaction of text fields
    auto_redact: bool = True

    # List of field names to exclude from auto-redaction
    auto_redact_exclude: list[str] = []

    # field_name: redaction_value. redaction_value can be a static value
    # or a db function, e.g. F("field_name") or Value("static value").
    custom_field_redactions: dict[str, Any] = {}

    class FieldRedactionStrategy(StrEnum):
        AUTO = "AUTO"
        CUSTOM = "CUSTOM"
        NONE = ""

    def is_field_redactable(self, field: models.Field) -> bool:
        """
        Return True if the field can be redacted.

        By default primary keys, relations, and choice fields cannot be
        redacted. Override this method to change this behaviour.

        """
        if field.is_relation:
            return False
        if getattr(field, "primary_key", False):
            return False
        if getattr(field, "choices", None):
            return False
        if getattr(field, "unique", None):
            return False
        return True

    def get_redactable_fields(self) -> list[models.Field]:
        """Return a list of fields on the model that are redactable."""
        return [f for f in self.get_model_fields() if self.is_field_redactable(f)]

    def field_redaction_strategy(self, field: models.Field) -> FieldRedactionStrategy:
        """Return the FieldRedaction value for a field."""
        if field.name in self.custom_field_redactions:
            return self.FieldRedactionStrategy.CUSTOM
        if self.get_field_auto_redacter(field):
            return self.FieldRedactionStrategy.AUTO
        return self.FieldRedactionStrategy.NONE

    def get_field_auto_redacter(
        self, field: models.Field
    ) -> Callable[[models.Field], Any] | None:
        """
        Return the auto redacter function for a field.

        Override this to provide global auto-redaction functions for
        your models.

        """
        if not self.auto_redact:
            return None
        if field.name in self.auto_redact_exclude:
            return None
        # will return None if the field isn't already handled by the
        # default redacters.
        return get_default_field_redacter(field)

    def get_auto_redaction_values(self) -> dict[str, Any]:
        """Return field:value dict for all auto-redactable fields."""
        # because None is a valid redaction value, we need to do this in
        # two passes - first get the redacter function, which _can_ be None,
        # then filter out the None values and call the redacter function
        # on the field.
        auto_redactors = {
            f: self.get_field_auto_redacter(f) for f in self.get_redactable_fields()
        }
        return {f.name: func(f) for f, func in auto_redactors.items() if func}

    def get_field_redaction_values(self) -> dict[str, Any]:
        """
        Return the redaction values for all field, custom or auto.

        This is a cascading lookup - start with all the auto-redaction
        values, then overwrite with the custom values.

        """
        vals = self.get_auto_redaction_values()
        vals.update(self.custom_field_redactions)
        return vals

    def redact_queryset(
        self,
        queryset: models.QuerySet[models.Model],
        **field_overrides: Any,
    ) -> int:
        """
        Redact a queryset (and SAVE).

        The `auto_redact` parameter will automatically redact all text
        fields with "X" if they are not already covered in the
        field_redactions dict.

        The `field_overrides` parameter allows you to pass in a dict of
        field_name: redaction_value to override any other redactions.

        The redactions cascade in the following order:

        - auto_redactions (all non-choice text fields)
        - field_redactions (static values set on the anonymiser)
        - field_overrides (values passed in to method)

        """
        redactions = self.get_field_redaction_values()
        redactions.update(field_overrides)
        return queryset.update(**redactions)


class ModelAnonymiser(AnonymiserBase, RedacterBase):
    """
    Base class for anonymisation functions.

    You can instantiate this class and call the anonymise_object method
    for any model as a "noop" anonymiser. It will not do anything, but
    it can be used to summarise field information in a consistent manner
    for models that do not need to be anonymised.

    """


@dataclasses.dataclass
class ModelFieldSummary:
    """
    Store info about the field and whether it is anonymisable.

    This is used to generate a summary of the fields on a model, and how
    they are anonymised / redacted - used to generate the documentation.

    """

    field: models.Field
    anonymiser: ModelAnonymiser | None = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # circ import
        from .registry import get_model_anonymiser

        self.anonymiser = get_model_anonymiser(self.model)

    @property
    def model(self) -> type[models.Model]:
        return self.field.model

    @property
    def app_label(self) -> str:
        return self.model._meta.app_label

    @property
    def model_name(self) -> str:
        return self.label.split(".")[-1]

    @property
    def label(self) -> str:
        return self.model._meta.label

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def field_type(self) -> str:
        return self.field.__class__.__name__

    @property
    def is_anonymised(self) -> bool:
        if self.anonymiser:
            return self.anonymiser.is_field_anonymised(self.field)
        return False

    @property
    def redaction_strategy(self) -> ModelAnonymiser.FieldRedactionStrategy:
        if self.anonymiser:
            return self.anonymiser.field_redaction_strategy(self.field)
        return ModelAnonymiser.FieldRedactionStrategy.NONE
