from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)
    location = models.CharField(max_length=255, blank=True)
    biography = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    extra_info = models.JSONField(default=dict)
