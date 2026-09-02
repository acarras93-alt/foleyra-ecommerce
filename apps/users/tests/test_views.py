import re
from urllib.parse import urlencode

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_anonymous_visitor_sees_registration_and_login_links(client):
    response = client.get(reverse("core:home"))

    content = response.content.decode()

    assert f'href="{reverse("users:register")}"' in content
    assert f'href="{reverse("users:login")}"' in content
    assert 'action="/accounts/logout/"' not in content


@pytest.mark.django_db
def test_authenticated_user_sees_a_csrf_protected_logout_form(client):
    user = get_user_model().objects.create_user(
        username="navigation-user",
        password="ReliablePassword000!",
    )
    client.force_login(user)

    response = client.get(reverse("core:home"))

    content = response.content.decode()

    assert f'<form method="post" action="{reverse("users:logout")}">' in content
    assert 'name="csrfmiddlewaretoken"' in content


@pytest.mark.parametrize("path", ["/accounts/register/", "/accounts/login/"])
def test_anonymous_visitor_receives_a_csrf_protected_authentication_form(client, path):
    response = client.get(path)

    content = response.content.decode()

    assert response.status_code == 200
    assert "<form" in content
    assert 'name="csrfmiddlewaretoken"' in content


@pytest.mark.django_db
def test_anonymous_visitor_can_register_as_an_active_unprivileged_user(client):
    response = client.post(
        "/accounts/register/",
        {
            "username": "registered-user",
            "password1": "ReliablePassword123!",
            "password2": "ReliablePassword123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("catalog:product-list")

    user = get_user_model().objects.get(username="registered-user")
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser
    assert not user.groups.exists()
    assert not user.user_permissions.exists()

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user == user


@pytest.mark.django_db
def test_registered_user_password_is_hashed(client):
    password = "ReliablePassword456!"

    client.post(
        "/accounts/register/",
        {
            "username": "hashed-password-user",
            "password1": password,
            "password2": password,
        },
    )

    user = get_user_model().objects.get(username="hashed-password-user")

    assert user.password != password
    assert user.check_password(password)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("existing_username", "registration_data"),
    [
        (
            "existing-user",
            {
                "username": "existing-user",
                "password1": "ReliablePassword789!",
                "password2": "ReliablePassword789!",
            },
        ),
        (
            None,
            {
                "username": "different-passwords-user",
                "password1": "ReliablePassword789!",
                "password2": "DifferentPassword789!",
            },
        ),
        (
            None,
            {
                "username": "weak-password-user",
                "password1": "12345678",
                "password2": "12345678",
            },
        ),
    ],
)
def test_invalid_registration_does_not_create_a_user_or_session(
    client, existing_username, registration_data
):
    user_model = get_user_model()
    if existing_username:
        user_model.objects.create_user(
            username=existing_username,
            password="ExistingPassword123!",
        )
    initial_user_count = user_model.objects.count()

    response = client.post("/accounts/register/", registration_data)

    assert response.status_code == 200
    assert user_model.objects.count() == initial_user_count
    assert response.wsgi_request.user.is_anonymous
    assert 'class="errorlist"' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "expected_url"),
    [
        ("/accounts/login/", reverse("catalog:product-list")),
        ("/accounts/login/?next=/", reverse("core:home")),
    ],
)
def test_anonymous_visitor_can_log_in_with_a_safe_internal_destination(
    client, path, expected_url
):
    user = get_user_model().objects.create_user(
        username="login-user",
        password="ReliablePassword987!",
    )

    response = client.post(
        path,
        {
            "username": user.username,
            "password": "ReliablePassword987!",
        },
    )

    assert response.status_code == 302
    assert response.url == expected_url

    destination_response = client.get(expected_url)

    assert destination_response.wsgi_request.user == user


@pytest.mark.django_db
@pytest.mark.parametrize(
    "next_url",
    [
        "https://external.example/",
        "//external.example/",
    ],
)
def test_login_ignores_an_external_or_unsafe_next_url(client, next_url):
    user = get_user_model().objects.create_user(
        username="external-next-user",
        password="ReliablePassword222!",
    )

    response = client.post(
        f"/accounts/login/?{urlencode({'next': next_url})}",
        {
            "username": user.username,
            "password": "ReliablePassword222!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("catalog:product-list")

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user == user


@pytest.mark.django_db
def test_invalid_credentials_show_a_generic_error_without_a_session(client):
    get_user_model().objects.create_user(
        username="existing-login-user",
        password="ReliablePassword111!",
    )

    unknown_user_response = client.post(
        "/accounts/login/",
        {"username": "unknown-user", "password": "ReliablePassword111!"},
    )
    wrong_password_response = client.post(
        "/accounts/login/",
        {"username": "existing-login-user", "password": "WrongPassword111!"},
    )

    for response in (unknown_user_response, wrong_password_response):
        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous

    error_pattern = r'<ul class="errorlist nonfield">\s*<li>([^<]+)</li>'
    unknown_user_error = re.search(
        error_pattern, unknown_user_response.content.decode()
    )
    wrong_password_error = re.search(
        error_pattern,
        wrong_password_response.content.decode(),
    )

    assert unknown_user_error is not None
    assert wrong_password_error is not None
    assert unknown_user_error.group(1) == wrong_password_error.group(1)


@pytest.mark.django_db
def test_authenticated_user_can_log_out_with_a_csrf_protected_post():
    user = get_user_model().objects.create_user(
        username="logout-user",
        password="ReliablePassword333!",
    )
    client = Client(enforce_csrf_checks=True)
    client.get("/accounts/login/")
    client.force_login(user)

    response = client.post(
        "/accounts/logout/",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )

    assert response.status_code == 302
    assert response.url == reverse("catalog:product-list")

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_logout_rejects_a_post_without_a_csrf_token_and_preserves_the_session():
    user = get_user_model().objects.create_user(
        username="csrf-logout-user",
        password="ReliablePassword555!",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post("/accounts/logout/")

    assert response.status_code == 403

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user == user


@pytest.mark.django_db
def test_anonymous_user_cannot_log_out_with_a_csrf_protected_post():
    client = Client(enforce_csrf_checks=True)
    client.get("/accounts/login/")
    session = client.session
    session["anonymous_marker"] = "preserved"
    session.save()
    session_key = session.session_key

    response = client.post(
        "/accounts/logout/",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )

    assert response.status_code == 403
    assert response.wsgi_request.user.is_anonymous
    assert client.session.session_key == session_key
    assert client.session["anonymous_marker"] == "preserved"


@pytest.mark.django_db
@pytest.mark.parametrize("authenticated", [False, True])
def test_get_logout_does_not_change_authentication_state(client, authenticated):
    user = get_user_model().objects.create_user(
        username="get-logout-user",
        password="ReliablePassword444!",
    )
    if authenticated:
        client.force_login(user)

    response = client.get("/accounts/logout/")

    assert response.status_code == 405

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user.is_authenticated is authenticated


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/accounts/register/", "/accounts/login/"])
def test_authenticated_user_is_redirected_from_authentication_forms(client, path):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="authenticated-user",
        password="ReliablePassword666!",
    )
    initial_user_count = user_model.objects.count()
    client.force_login(user)

    response = client.get(path)

    assert response.status_code == 302
    assert response.url == reverse("catalog:product-list")
    assert user_model.objects.count() == initial_user_count

    catalog_response = client.get(reverse("catalog:product-list"))

    assert catalog_response.wsgi_request.user == user
