from __future__ import annotations

import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Iterator, TypeAlias

from django.db import models

# (old_value, new_value) tuple
AnonymisationResult: TypeAlias = tuple[Any, Any]

# Store info about the field and whether it is anonymisable
FieldSummaryTuple = namedtuple(
    "FieldSummaryTuple", ("app", "model", "field", "type", "is_anonymisable")
)

logger = logging.getLogger(__name__)


@dataclass
class FieldSummaryData:
    field: models.Field
    is_anonymisable: bool

    @property
    def model_label(self) -> str:
        return self.field.model._meta.label

    @property
    def app(self) -> str:
        return self.field.model._meta.app_label

    @property
    def model(self) -> str:
        return self.field.model._meta.object_name or ""

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def field_type(self) -> str:
        return self.field.__class__.__name__


def get_field_summary_data(
    field: models.Field, anonymiser: ModelAnonymiser | None
) -> FieldSummaryData:
    if anonymiser:
        return FieldSummaryData(field, anonymiser.is_field_anonymisable(field.name))
    return FieldSummaryData(field, False)


class _ModelBase:
    # Override with the model to be anonymised
    model: type[models.Model]

    def get_model_fields(self) -> list[models.Field]:
        """Return a list of fields on the model."""
        if not self.model:
            raise NotImplementedError("model must be set")
        return [
            f
            for f in self.model._meta.get_fields()
            if not isinstance(f, models.ForeignObjectRel)
        ]


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

    def get_model_field_summary(self) -> list[FieldSummaryData]:
        """Return a list of all model fiels and whether they are anonymisable."""
        return [
            FieldSummaryData(f, self.is_field_anonymisable(f.name))
            for f in self.get_model_fields()
        ]

    def is_field_anonymisable(self, field_name: str) -> bool:
        return hasattr(self, f"anonymise_{field_name}")

    def get_anonymisable_fields(self) -> list[models.Field]:
        """Return a list of fields on the model that are anonymisable."""
        return [
            f for f in self.get_model_fields() if self.is_field_anonymisable(f.name)
        ]

    def anonymise_field(
        self, obj: models.Model, field_name: str
    ) -> AnonymisationResult:
        """Anonymise a single field on the model instance."""
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
            output[field.name] = self.anonymise_field(obj, field.name)
        self.post_anonymise_object(obj, **output)

    def anonymise_queryset(self, queryset: Iterator[models.Model]) -> int:
        """Anonymise all objects in the queryset (and SAVE)."""
        count = 0
        for obj in queryset:
            self.anonymise_object(obj)
            obj.save()
            count += 1
        return count

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

    def is_field_auto_redactable(self, field: models.Field) -> bool:
        """
        Return True if the field should be auto-redacted.

        Currently this includes text fields that are not choices, primary
        keys, unique fields, or in the auto_redact_exclude list.

        """
        return (
            isinstance(field, (models.CharField, models.TextField))
            and not field.choices
            and not field.primary_key
            and not getattr(field, "unique", False)
            and field.name not in self.auto_redact_exclude
        )

    def auto_field_redactions(self) -> dict[str, str]:
        """
        Return a dict of redaction_values for all text fields.

        This is used to "auto-redact" all char/text fields with "X" - if
        the field does not use choices, and is not a primary key or
        unique field.

        """

        def _max_length(f: models.Field) -> int:
            if isinstance(f, models.CharField):
                return f.max_length
            if isinstance(f, models.TextField):
                return 400
            raise ValueError("Field must be CharField or TextField")

        return {
            f.name: _max_length(f) * "X"
            for f in self.get_model_fields()
            if self.is_field_auto_redactable(f)
        }

    def redact_queryset(
        self,
        queryset: models.QuerySet[models.Model],
        auto_redact: bool = auto_redact,
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
        redactions: dict[str, Any] = {}
        if auto_redact:
            redactions.update(self.auto_field_redactions())
        redactions.update(self.custom_field_redactions)
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

    # # Override with the model to be anonymised
    # model: type[models.Model]

    # # Set to False to disable auto-redaction of text fields
    # auto_redact: bool = True

    # # List of field names to exclude from auto-redaction
    # auto_redact_exclude: list[str] = []

    # # field_name: redaction_value. redaction_value can be a static value
    # # or a db function, e.g. F("field_name") or Value("static value").
    # custom_field_redactions: dict[str, Any] = {}

    # def __setattr__(self, __name: str, __value: Any) -> None:
    #     """
    #     Prevent setting of attribute on the anonymiser itself.

    #     This is a common mistake when writing anonymiser functions -
    #     inside the `anonymise_FOO` method you call `self.FOO = "bar"`
    #     instead of `obj.FOO = "bar"`, because that's the natural way to
    #     write it.

    #     This will raise an AttributeError if you try to set an attribute
    #     that looks like it maps to an anonymiser method.

    #     """
    #     if hasattr(self, f"anonymise_{__name}"):
    #         raise AttributeError(
    #             "Cannot set anonymiser attributes directly - did you mean to "
    #             "use 'obj' instead of 'self' in method "
    #             f"`{self.__class__.__name__}.anonymise_{__name}`?"
    #         )
    #     super().__setattr__(__name, __value)

    # def get_model_fields(self) -> list[models.Field]:
    #     """Return a list of fields on the model."""
    #     if not self.model:
    #         raise NotImplementedError("model must be set")
    #     return [
    #         f
    #         for f in self.model._meta.get_fields()
    #         if not isinstance(f, models.ForeignObjectRel)
    #     ]

    # def get_model_field_summary(self) -> list[FieldSummaryData]:
    #     """Return a list of all model fiels and whether they are anonymisable."""
    #     return [
    #         FieldSummaryData(f, self.is_field_anonymisable(f.name))
    #         for f in self.get_model_fields()
    #     ]

    # def is_field_anonymisable(self, field_name: str) -> bool:
    #     return hasattr(self, f"anonymise_{field_name}")

    # def get_anonymisable_fields(self) -> list[models.Field]:
    #     """Return a list of fields on the model that are anonymisable."""
    #     return [
    #         f for f in self.get_model_fields() if self.is_field_anonymisable(f.name)
    #     ]

    # def anonymise_field(
    #     self, obj: models.Model, field_name: str
    # ) -> AnonymisationResult:
    #     """Anonymise a single field on the model instance."""
    #     if not (anon_func := getattr(self, f"anonymise_{field_name}", None)):
    #         raise NotImplementedError(
    #             f"Anonymiser function 'anonymise_{field_name}' not implemented"
    #         )
    #     old_value = getattr(obj, field_name)
    #     anon_func(obj)
    #     new_value = getattr(obj, field_name)
    #     return old_value, new_value

    # def anonymise_object(self, obj: models.Model) -> None:
    #     """Anonymise the model instance (NOT THREAD SAFE)."""
    #     output = {}
    #     for field in self.get_anonymisable_fields():
    #         output[field.name] = self.anonymise_field(obj, field.name)
    #     self.post_anonymise_object(obj, **output)

    # def anonymise_queryset(self, queryset: Iterator[models.Model]) -> int:
    #     """Anonymise all objects in the queryset (and SAVE)."""
    #     count = 0
    #     for obj in queryset:
    #         self.anonymise_object(obj)
    #         obj.save()
    #         count += 1
    #     return count

    # def post_anonymise_object(
    #     self, obj: models.Model, **updates: AnonymisationResult
    # ) -> None:
    #     """
    #     Post-process the model instance after anonymisation.

    #     The updates param is a dict of field names to (old_value, new_value) tuples.

    #     """
    #     pass

    # def is_field_auto_redactable(self, field: models.Field) -> bool:
    #     """
    #     Return True if the field should be auto-redacted.

    #     Currently this includes text fields that are not choices, primary
    #     keys, unique fields, or in the auto_redact_exclude list.

    #     """
    #     return (
    #         isinstance(field, (models.CharField, models.TextField))
    #         and not field.choices
    #         and not field.primary_key
    #         and not getattr(field, "unique", False)
    #         and field.name not in self.auto_redact_exclude
    #     )

    # def auto_field_redactions(self) -> dict[str, str]:
    #     """
    #     Return a dict of redaction_values for all text fields.

    #     This is used to "auto-redact" all char/text fields with "X" - if
    #     the field does not use choices, and is not a primary key or
    #     unique field.

    #     """

    #     def _max_length(f: models.Field) -> int:
    #         if isinstance(f, models.CharField):
    #             return f.max_length
    #         if isinstance(f, models.TextField):
    #             return 400
    #         raise ValueError("Field must be CharField or TextField")

    #     return {
    #         f.name: _max_length(f) * "X"
    #         for f in self.get_model_fields()
    #         if self.is_field_auto_redactable(f)
    #     }

    # def redact_queryset(
    #     self,
    #     queryset: models.QuerySet[models.Model],
    #     auto_redact: bool = auto_redact,
    #     **field_overrides: Any,
    # ) -> int:
    #     """
    #     Redact a queryset (and SAVE).

    #     The `auto_redact` parameter will automatically redact all text
    #     fields with "X" if they are not already covered in the
    #     field_redactions dict.

    #     The `field_overrides` parameter allows you to pass in a dict of
    #     field_name: redaction_value to override any other redactions.

    #     The redactions cascade in the following order:

    #     - auto_redactions (all non-choice text fields)
    #     - field_redactions (static values set on the anonymiser)
    #     - field_overrides (values passed in to method)

    #     """
    #     redactions: dict[str, Any] = {}
    #     if auto_redact:
    #         redactions.update(self.auto_field_redactions())
    #     redactions.update(self.custom_field_redactions)
    #     redactions.update(field_overrides)
    #     return queryset.update(**redactions)
