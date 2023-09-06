from typing import Any

from django.core.management.base import BaseCommand

from anonymise.models import AnonymisableModel


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        self.stdout.write("Anonymising model objects...")
        self.stdout.write("app | model | field | type | is_anonymisable")
        self.stdout.write("--- | --- | --- | --- | ---")
        for model in AnonymisableModel.get_subclasses():
            field_summary = model.get_anonymisable_fields_summary()
            for field in field_summary:
                self.stdout.write(
                    f"{field.app} | {field.model} | {field.field} | {field.type} | "
                    f"{field.is_anonymisable}"
                )
        return None
