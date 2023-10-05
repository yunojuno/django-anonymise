from __future__ import annotations

from collections import namedtuple
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from anonymiser import registry

ModelAnonymiserSummary = namedtuple(
    "ModelAnonymiserSummary",
    ["model", "anonymiser"],
)


def get_model_anonymisers() -> list[ModelAnonymiserSummary]:
    """
    Return model_name: anonymiser_name for all models.

    Return the names, not the objects, as Django templates cannnot access
    _meta attributes of models, and all we need is the name.

    """
    output = []
    for m in apps.get_models():
        if m._meta.abstract:
            continue
        if anonymiser := registry.get_model_anonymiser(m):
            output.append(
                ModelAnonymiserSummary(
                    m._meta.model_name,
                    anonymiser.__class__.__name__,
                )
            )
        else:
            output.append(ModelAnonymiserSummary(m._meta.label, ""))
    return output


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        out = render_to_string(
            "anonymiser/display_model_anonymisation.md",
            {
                "model_anonymisers": get_model_anonymisers(),
                "model_fields": registry.get_all_model_fields(),
            },
        )
        self.stdout.write(out)
