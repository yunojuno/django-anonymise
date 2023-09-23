from django.db.models import F, Value
from django.db.models.functions import Concat

from anonymiser.decorators import register_anonymiser
from anonymiser.models import AnonymiserBase, ModelAnonymiser, RedacterBase

from .models import User


@register_anonymiser
class UserAnonymiser(ModelAnonymiser):
    model = User
    auto_redact = True

    custom_field_redactions = {
        "first_name": "FIRST_NAME",
    }

    def anonymise_first_name(self, obj: User) -> None:
        obj.first_name = "Anonymous"


class BadUserAnonymiser(AnonymiserBase):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        # this is not allowed - should be obj.first_name.
        self.first_name = "Anonymous"


class UserRedacter(RedacterBase):
    model = User

    custom_field_redactions = {
        "first_name": "FIRST_NAME",
        "last_name": "LAST_NAME",
        "email": Concat(Value("user_"), F("id"), Value("@example.com")),
    }
