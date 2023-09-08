from anonymiser.decorators import register_anonymiser
from anonymiser.models import BaseAnonymiser

from .models import User


@register_anonymiser
class UserAnonymiser(BaseAnonymiser):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        obj.first_name = "Anonymous"
