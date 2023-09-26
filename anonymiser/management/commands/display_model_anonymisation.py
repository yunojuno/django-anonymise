from typing import Any

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from anonymiser import registry


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        model_fields = registry.get_all_model_fields()
        out = render_to_string(
            "display_model_anonymisation.md",
            {"model_fields": model_fields},
        )
        self.stdout.write(out)
