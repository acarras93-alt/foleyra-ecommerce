import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection


@pytest.mark.django_db
def test_project_uses_postgresql():
    assert connection.vendor == "postgresql"


def test_project_uses_custom_user():
    assert get_user_model()._meta.label == "users.User"


def test_project_uses_json_only_drf_defaults_without_authentication():
    assert settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] == [
        "rest_framework.renderers.JSONRenderer"
    ]
    assert settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == []
