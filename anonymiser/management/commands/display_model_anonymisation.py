from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.template.loader import render_to_string

from anonymiser.registry import get_model_anonymiser


class Command(BaseCommand):
    def get_models(self) -> list[type[Model]]:
        """Force alphabetical order of models."""
        return sorted(apps.get_models(), key=lambda m: m._meta.label)

    def handle(self, *args: Any, **options: Any) -> None:
        for model in self.get_models():
            if anonymiser := get_model_anonymiser(model):
                data = anonymiser.get_model_field_summary()
        out = render_to_string(
            "display_model_anonymisation.md",
            {"anonymised_models": data},
        )
        self.stdout.write(out)
