import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class anonymiserConfig(AppConfig):
    name = "anonymiser"
    verbose_name = "Django Model Anonymiser"

    def ready(self) -> None:
        super().ready()
        logger.debug("Initialising anonymisation registry")
        from . import registry  # noqa F401
