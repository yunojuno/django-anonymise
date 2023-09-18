from django.db import models
from django.db.models.functions import Concat

from anonymiser.db.expressions import GenerateUuid4
from anonymiser.decorators import register_anonymiser
from anonymiser.models import BaseAnonymiser

from .models import User


@register_anonymiser
class UserAnonymiser(BaseAnonymiser):
    model = User
    field_redactions = {
        "first_name": "FIRST_NAME",
        "last_name": "LAST_NAME",
        "uuid": GenerateUuid4(),
        "email": Concat(
            models.F("first_name"),
            models.Value("."),
            models.F("last_name"),
            models.Value("@example.com"),
        ),
    }

    def anonymise_first_name(self, obj: User) -> None:
        obj.first_name = "Anonymous"


class BadUserAnonymiser(BaseAnonymiser):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        # this is not allowed - should be obj.first_name.
        self.first_name = "Anonymous"
