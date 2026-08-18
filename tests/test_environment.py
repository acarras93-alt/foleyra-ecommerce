import pytest
from django.contrib.auth import get_user_model
from django.db import connection


@pytest.mark.django_db
def test_project_uses_postgresql():
    assert connection.vendor == "postgresql"


def test_project_uses_custom_user():
    assert get_user_model()._meta.label == "users.User"
