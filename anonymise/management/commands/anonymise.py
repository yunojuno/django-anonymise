from typing import Any

from django.core.management.base import BaseCommand

from anonymise.models import anonymisable_models, model_fields_summary


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        self.stdout.write("Anonymising model objects...")
        self.stdout.write("app | model | field | type | is_anonymisable")
        self.stdout.write("--- | --- | --- | --- | ---")
        for model in anonymisable_models():
            field_summary = model_fields_summary(model)
            for field in field_summary:
                self.stdout.write(
                    f"{field.app} | {field.model} | {field.field} | {field.type} | "
                    f"{field.is_anonymisable}"
                )
        return None
