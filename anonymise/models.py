import logging
from collections import namedtuple
from typing import Any, TypeAlias

from django.apps import apps as django_apps
from django.db import models

# from django.utils.timezone import now as tz_now

# (old_value, new_value) tuple
AnonymisationResult: TypeAlias = tuple[Any, Any]

# Store info about the field and whether it is anonymisable
FieldSummaryTuple = namedtuple(
    "FieldSummaryTuple", ("app", "model", "field", "type", "is_anonymisable")
)

logger = logging.getLogger(__name__)


class AnonymisableModel(models.Model):
    """Model mixin that adds anonymisation functionality."""

    # used to format the expected anonymisation function name
    ANONYMISE_FIELD_PATTERN = "anonymise_{field_name}_field"

    # anonymised_at = models.DateTimeField(
    #     blank=True, null=True, verbose_name="Object anonymisation timestamp."
    # )

    class Meta:
        abstract = True

    @classmethod
    def get_subclasses(cls) -> list[type[models.Model]]:
        return [m for m in django_apps.get_models() if issubclass(m, AnonymisableModel)]

    @classmethod
    def is_field_anonymisable(cls, field: models.Field) -> bool:
        if isinstance(field, (models.AutoField, models.ForeignObjectRel)):
            return False
        func_name = cls.ANONYMISE_FIELD_PATTERN.format(field_name=field.name)
        return hasattr(cls, func_name)

    @classmethod
    def get_anonymisable_fields(cls) -> list[models.Field]:
        """
        Return a list of fields that can be anonymised.

        This is the full list of anonymisable fields, based on whether
        they have a custom anonymisation method defined. It does not
        take into account any include/exclude lists.

        NB ForeignObjectRel is a subclass of Field, but we don't want
        to anonymise them (here), so we filter them out.

        """
        return [
            f
            for f in cls._meta.get_fields()
            if not isinstance(f, models.ForeignObjectRel)
            and cls.is_field_anonymisable(f)
        ]

    @classmethod
    def get_anonymisable_fields_summary(cls) -> list[FieldSummaryTuple]:
        """Return tabular summary of all fields and whether they are anonymisable."""
        return sorted(
            [
                FieldSummaryTuple(
                    cls._meta.app_label,
                    cls.__name__,
                    f.name,
                    f.__class__.__name__,
                    cls.is_field_anonymisable(f),
                )
                for f in cls._meta.get_fields()
                if not isinstance(f, models.ForeignObjectRel)
            ],
            key=lambda x: x.app + x.model + x.type + x.field,
        )

    def post_anonymise(self, **updates: AnonymisationResult) -> None:
        """
        Post-process the model after anonymisation.

        Sometimes it may be necessary to perform additional processing
        on the model after anonymisation. This method is called after
        all fields have been anonymised, and is passed a dictionary of
        field names to tuples of (old_value, new_value) for each field
        that was anonymised.

        """
        pass

    def anonymise_field(self, field: models.Field) -> AnonymisationResult:
        """Anonymise a single field."""
        logger.debug("Anonymising %s.%s.%s", self._meta.label, self.pk, field.name)
        func_name = self.ANONYMISE_FIELD_PATTERN.format(field_name=field.name)
        if not (_anonymise_field := getattr(self, func_name, None)):
            raise NotImplementedError(f"{func_name} not implemented")
        old_value = getattr(self, field.name)
        _anonymise_field()
        new_value = getattr(self, field.name)
        return old_value, new_value

    def anonymise_fields(self, *fields: models.Field) -> dict[str, AnonymisationResult]:
        """Anonymise a list of fields."""
        return {f.name: self.anonymise_field(f) for f in fields}

    def anonymise(self) -> None:
        """Anonymise all model object fields."""
        logger.debug("Anonymising %s.%s", self._meta.label, self.pk)
        updates = self.anonymise_fields(*self.get_anonymisable_fields())
        self.post_anonymise(**updates)
        # self.anonymised_at = tz_now()
