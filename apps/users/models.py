"""User models."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Project user, intentionally extensible from the first migration."""
