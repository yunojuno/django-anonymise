from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import ForeignObjectRel, Model
from django.template.loader import render_to_string

from anonymiser.models import FieldSummaryData
from anonymiser.registry import get_model_anonymiser


class Command(BaseCommand):
    def get_models(self) -> list[type[Model]]:
        """Force alphabetical order of models."""
        return sorted(apps.get_models(), key=lambda m: m._meta.label)

    def get_fields(self, model: type[Model]) -> list:
        """Get model fields ordered by type and then name."""
        return sorted(
            [
                f
                for f in model._meta.get_fields()
                if not isinstance(f, ForeignObjectRel)
            ],
            key=lambda f: f.__class__.__name__ + f.name,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        model_fields: list[FieldSummaryData] = []
        model_anonymisers: dict[str, str] = {}
        for model in self.get_models():
            model_name = model._meta.label
            anonymiser = get_model_anonymiser(model)
            anonymiser_name = anonymiser.__class__.__name__ if anonymiser else ""
            model_anonymisers[model_name] = anonymiser_name
            for f in self.get_fields(model):
                is_anonymisable = False
                if anonymiser:
                    is_anonymisable = anonymiser.is_field_anonymisable(f.name)
                field_data = FieldSummaryData(f, is_anonymisable)
                model_fields.append(field_data)
        out = render_to_string(
            "display_model_anonymisation.md",
            {"model_anonymisers": model_anonymisers, "model_fields": model_fields},
        )
        self.stdout.write(out)
