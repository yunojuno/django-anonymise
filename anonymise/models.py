from typing import Any, TypeAlias

from django.db import models

# (old_value, new_value) tuple
AnonymisationResult: TypeAlias = tuple[Any, Any]


class AnonymisableModel(models.Model):
    """Model mixin that adds anonymisation functionality."""

    # used to format the expected anonymisation function name
    ANONYMISE_FIELD_PATTERN = "anonymise_{field_name}_field"

    class Meta:
        abstract = True

    @classmethod
    def _is_anonymisable(cls, field: models.Field) -> bool:
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
            if not isinstance(f, models.ForeignObjectRel) and cls._is_anonymisable(f)
        ]

    def post_anonymise(self, **updates: AnonymisationResult) -> None:
        """
        Post-process the model after anonymisation.

        Sometimes it may be necessary to perform additional processing
        on the model after anonymisation. This method is called after
        all fields have been anonymised, and is passed a dictionary of
        field names to tuples of (old_value, new_value) for each field
        that was anonymised..

        """
        pass

    def anonymise_field(self, field: models.Field) -> AnonymisationResult:
        """Anonymise a single field."""
        func_name = self.ANONYMISE_FIELD_PATTERN.format(field.name)
        if not getattr(self, func_name):
            raise NotImplementedError(f"{func_name} not implemented")
        old_value = getattr(self, field.name)
        new_value = getattr(self, func_name)()
        return old_value, new_value

    def anonymise_fields(self, *fields: models.Field) -> dict[str, AnonymisationResult]:
        """Anonymise a list of fields."""
        updates = {}
        for f in fields:
            old_value = getattr(self, f.name)
            self.anonymise_field(f)
            new_value = getattr(self, f.name)
            updates[f.name] = (old_value, new_value)
        return updates

    def anonymise(self) -> None:
        """Anonymise all model object fields."""
        updates = self.anonymise_fields(*self.get_anonymisable_fields())
        self.post_anonymise(*updates)
