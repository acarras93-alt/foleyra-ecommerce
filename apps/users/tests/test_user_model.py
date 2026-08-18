import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.users.models import User


def test_custom_user_model_is_configured():
    assert settings.AUTH_USER_MODEL == "users.User"
    assert get_user_model() is User


def test_postgresql_is_the_only_configured_database_backend():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


@pytest.mark.django_db
def test_custom_user_can_be_persisted():
    user = User.objects.create_user(username="test-user", password="test-password")

    saved_user = User.objects.get(pk=user.pk)

    assert saved_user.username == "test-user"
    assert saved_user.check_password("test-password")
