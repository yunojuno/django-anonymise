from collections import defaultdict
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from anonymiser.models import FieldSummaryData
from anonymiser.registry import get_model_anonymiser


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        models = defaultdict(list)
        for model in apps.get_models():
            anonymiser = get_model_anonymiser(model)
            for f in model._meta.get_fields():
                is_anonymisable = (
                    anonymiser.is_field_anonymisable(f.name) if anonymiser else False
                )
                field_data = FieldSummaryData(f, is_anonymisable)
                models[field_data.model_label].append(field_data)
        out = render_to_string(
            "display_model_anonymisation.md", {"models": dict(models)}
        )
        self.stdout.write(out)
