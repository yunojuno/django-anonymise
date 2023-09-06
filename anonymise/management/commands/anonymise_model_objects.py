from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandParser

from anonymise.models import AnonymisableModel


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Commit changes to the database (call save on each object).",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        self.stdout.write("Anonymising model objects...")
        self.stdout.write("app | model | field | type | is_anonymisable")
        self.stdout.write("--- | --- | --- | --- | ---")
        for model in [m for m in apps.get_models() if issubclass(m, AnonymisableModel)]:
            field_summary = model.get_anonymisable_fields_summary()
            for field in field_summary:
                self.stdout.write(
                    f"{field.app} | {field.model} | {field.field} | {field.type} | "
                    f"{field.is_anonymisable}"
                )
        return None
