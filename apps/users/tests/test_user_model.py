import pytest

from apps.users.models import User


@pytest.mark.django_db
def test_custom_user_can_be_persisted():
    user = User.objects.create_user(username="test-user", password="test-password")

    saved_user = User.objects.get(pk=user.pk)

    assert saved_user.username == "test-user"
    assert saved_user.check_password("test-password")
