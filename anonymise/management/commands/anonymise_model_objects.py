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
        for model in [m for m in apps.get_models() if issubclass(m, AnonymisableModel)]:
            self.stdout.write(f"Anonymising {model.__name__}...")
            self.stdout.write(f"Anonymising {model._meta.label}...")
            anon_fields = model.get_anonymisable_fields()
            all_fields = sorted(model._meta.get_fields(), key=lambda f: f.name)
            for field in all_fields:
                self.stdout.write(
                    f"... {model._meta.label}.{field.name} | "
                    f"{field.__class__.__name__} | "
                    f"{field.is_relation} | {field in anon_fields}"
                )
        return None
