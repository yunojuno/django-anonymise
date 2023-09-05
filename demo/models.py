from django.contrib.auth.models import AbstractUser

from anonymise.models import AnonymisableModel


class User(AnonymisableModel, AbstractUser):
    def anonymise_first_name_field(self) -> None:
        self.first_name = "Anonymous"
