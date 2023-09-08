from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand

from anonymiser.models import FieldSummaryData
from anonymiser.registry import get_model_anonymiser


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            "Outputting all models and fields, and their anonymisability\n---"
        )
        for model in apps.get_models():
            anonymiser = get_model_anonymiser(model)
            suffix = f"({anonymiser.__class__.__name__})" if anonymiser else ""
            self.stdout.write(f"{model._meta.label} {suffix}")
            self.stdout.write("")
            for f in model._meta.get_fields():
                is_anonymisable = (
                    anonymiser.is_field_anonymisable(f.name) if anonymiser else False
                )
                field_data = FieldSummaryData(f, is_anonymisable)
                self.stdout.write(
                    f"  {field_data.field_name}, {field_data.field_type}, "
                    f"{field_data.is_anonymisable}"
                )
            self.stdout.write("")
