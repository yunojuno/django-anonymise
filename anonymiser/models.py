import logging
from collections import namedtuple
from typing import Any, TypeAlias

from django.db import models
from django.template.loader import render_to_string

# (old_value, new_value) tuple
AnonymisationResult: TypeAlias = tuple[Any, Any]

# Store info about the field and whether it is anonymisable
FieldSummaryTuple = namedtuple(
    "FieldSummaryTuple", ("app", "model", "field", "type", "is_anonymisable")
)

logger = logging.getLogger(__name__)


class BaseAnonymiser:
    """Base class for anonymisation functions."""

    model: type[models.Model] | None = None

    def get_model_fields(self) -> list[models.Field]:
        """Return a list of fields on the model."""
        if not self.model:
            raise NotImplementedError("model must be set")
        return [
            f
            for f in self.model._meta.get_fields()
            if not isinstance(f, models.ForeignObjectRel)
        ]

    def get_model_field_summary(self) -> list[FieldSummaryTuple]:
        """Return a list of all model fiels and whether they are anonymisable."""
        return [
            FieldSummaryTuple(
                app=f.model._meta.app_label,
                model=f.model._meta.object_name,
                field=f.name,
                type=f.__class__.__name__,
                is_anonymisable=self.is_field_anonymisable(f.name),
            )
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

    def anonymise_queryset(self, queryset: models.QuerySet) -> None:
        """Anonymise all objects in the queryset (and SAVE)."""
        for obj in queryset:
            self.anonymise_object(obj)
            obj.save()

    def post_anonymise_object(
        self, obj: models.Model, **updates: AnonymisationResult
    ) -> None:
        """
        Post-process the model instance after anonymisation.

        The updates param is a dict of field names to (old_value, new_value) tuples.

        """
        pass

    def print_summary(self, template_name: str = "field_summary.md") -> str:
        """Print a summary of the anonymiser model fields."""
        return render_to_string(
            template_name,
            {
                "fields": self.get_model_field_summary(),
            },
        )
