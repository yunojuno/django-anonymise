from anonymiser.decorators import register_anonymiser
from anonymiser.models import BaseAnonymiser

from .models import User


@register_anonymiser
class UserAnonymiser(BaseAnonymiser):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        obj.first_name = "Anonymous"


class BadUserAnonymiser(BaseAnonymiser):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        # this is not allowed - should be obj.first_name.
        self.first_name = "Anonymous"
