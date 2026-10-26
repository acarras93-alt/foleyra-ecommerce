import pytest
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from apps.catalog.models import Category


def grant_permission(user, *, model, codename):
    content_type = ContentType.objects.get_for_model(model)
    permission = Permission.objects.get(
        content_type=content_type,
        codename=codename,
    )
    user.user_permissions.add(permission)


@pytest.mark.django_db
def test_anonymous_user_is_redirected_to_admin_login(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url == "/admin/login/?next=/admin/"


@pytest.mark.django_db
def test_authenticated_non_staff_user_cannot_access_admin(client):
    user = get_user_model().objects.create_user(
        username="admin-non-staff",
        password="ReliablePassword123!",
    )
    client.force_login(user)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url == "/admin/login/?next=/admin/"


@pytest.mark.django_db
def test_staff_user_without_model_permission_cannot_open_catalog_model(client):
    user = get_user_model().objects.create_user(
        username="admin-without-permission",
        password="ReliablePassword123!",
        is_staff=True,
    )
    client.force_login(user)

    response = client.get(reverse("admin:catalog_category_changelist"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_user_with_view_only_permission_cannot_modify_catalog_entity(client):
    category = Category.objects.create(
        name="Administración",
        slug="administracion",
    )
    user = get_user_model().objects.create_user(
        username="admin-view-only",
        password="ReliablePassword123!",
        is_staff=True,
    )
    grant_permission(user, model=Category, codename="view_category")
    client.force_login(user)

    change_url = reverse(
        "admin:catalog_category_change",
        args=[category.pk],
    )
    get_response = client.get(change_url)
    post_response = client.post(
        change_url,
        {
            "name": "Cambio no autorizado",
            "slug": category.slug,
            "description": category.description,
            "is_active": "on",
        },
    )

    category.refresh_from_db()
    assert get_response.status_code == 200
    assert post_response.status_code == 403
    assert category.name == "Administración"


@pytest.mark.django_db
def test_valid_admin_changes_create_log_entries_with_actor_object_and_action(client):
    user = get_user_model().objects.create_user(
        username="admin-audited",
        password="ReliablePassword123!",
        is_staff=True,
    )
    grant_permission(user, model=Category, codename="add_category")
    grant_permission(user, model=Category, codename="change_category")
    grant_permission(user, model=Category, codename="view_category")
    client.force_login(user)

    add_response = client.post(
        reverse("admin:catalog_category_add"),
        {
            "name": "Categoría auditada",
            "slug": "categoria-auditada",
            "description": "Alta registrada.",
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    category = Category.objects.get(slug="categoria-auditada")
    change_response = client.post(
        reverse("admin:catalog_category_change", args=[category.pk]),
        {
            "name": "Categoría auditada actualizada",
            "slug": category.slug,
            "description": category.description,
            "is_active": "on",
            "_save": "Guardar",
        },
    )
    category.refresh_from_db()

    content_type = ContentType.objects.get_for_model(Category)
    entries = LogEntry.objects.filter(
        user_id=user.pk,
        content_type=content_type,
        object_id=str(category.pk),
    ).order_by("action_time")
    assert add_response.status_code == 302
    assert change_response.status_code == 302
    assert list(entries.values_list("action_flag", flat=True)) == [
        ADDITION,
        CHANGE,
    ]
    assert entries.last().object_repr == str(category)
