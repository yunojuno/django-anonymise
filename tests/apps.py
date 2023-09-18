import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TestsConfig(AppConfig):
    name = "tests"
    verbose_name = "Django Model Anonymiser Test App"

    def ready(self) -> None:
        super().ready()
        logger.debug("Adding tests app anonymisers")
        from . import anonymisers  # noqa F401
