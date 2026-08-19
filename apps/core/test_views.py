from django.urls import reverse


def test_home_url_is_reversible_at_root():
    assert reverse("core:home") == "/"


def test_home_is_public_and_returns_success(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200


def test_home_displays_its_public_heading(client):
    response = client.get(reverse("core:home"))

    assert "Paquetes sonoros para proyectos audiovisuales" in response.content.decode()
