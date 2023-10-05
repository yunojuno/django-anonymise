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
    help = "Display anonymisation configuration"  # noqa: A003

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "-t",
            "--template",
            default="anonymisation_config.md",
            help=(
                "Template to use for output (defaults to " "anonymisation_config.md)."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        template_name = options["template"]
        out = render_to_string(
            f"anonymiser/{template_name}",
            {
                "model_anonymisers": get_model_anonymisers(),
                "model_fields": registry.get_all_model_fields(),
            },
        )
        self.stdout.write(out)
