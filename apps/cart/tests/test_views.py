from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.cart.services import add_offer_to_cart
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


def create_available_offer():
    category = Category.objects.create(name="Ambientes", slug="ambientes")
    product = Product.objects.create(
        category=category,
        name="Nocturnos urbanos",
        slug="nocturnos-urbanos",
        sku="AMB-001",
        summary="Ambiente ficticio de ciudad durante la noche.",
        description="Grabación preparada para una producción audiovisual.",
        duration_ms=18_500,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    license_type = LicenseType.objects.create(
        name="YouTube y redes sociales",
        slug="youtube-redes-sociales",
        usage_scope="Un canal por plataforma",
        summary="Uso en contenido propio para redes sociales.",
        terms_version="1.0",
    )
    return ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )


def test_anonymous_visitor_is_redirected_to_login_when_opening_cart(client):
    response = client.get("/cart/")

    assert response.status_code == 302
    assert response.url == f"{reverse('users:login')}?next=/cart/"


@pytest.mark.django_db
def test_anonymous_cart_addition_without_csrf_token_is_forbidden():
    client = Client(enforce_csrf_checks=True)
    offer = create_available_offer()

    response = client.post(reverse("cart:add-item"), {"offer_id": offer.pk})

    assert response.status_code == 403
    assert not Cart.objects.exists()


@pytest.mark.django_db
def test_anonymous_cart_addition_with_csrf_token_redirects_without_changes():
    client = Client(enforce_csrf_checks=True)
    offer = create_available_offer()
    client.get(reverse("users:login"))
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        reverse("cart:add-item"),
        {"offer_id": offer.pk, "csrfmiddlewaretoken": csrf_token},
    )

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('users:login')}?next=/cart/"
    assert not Cart.objects.exists()


@pytest.mark.django_db
def test_authenticated_user_cannot_add_offer_with_get(client):
    user = get_user_model().objects.create_user(
        username="get-add-user",
        password="ReliablePassword123!",
    )
    client.force_login(user)

    response = client.get(reverse("cart:add-item"))

    assert response.status_code == 405
    assert not Cart.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_authenticated_user_without_cart_sees_an_empty_cart_without_creating_one(
    client,
):
    user = get_user_model().objects.create_user(
        username="empty-cart-user",
        password="ReliablePassword123!",
    )
    client.force_login(user)

    response = client.get("/cart/")

    assert response.status_code == 200
    assert "Tu carrito está vacío." in response.content.decode()
    assert not Cart.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_authenticated_user_can_add_an_available_offer_to_cart(client):
    user = get_user_model().objects.create_user(
        username="adding-cart-user",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    client.force_login(user)

    response = client.post(reverse("cart:add-item"), {"offer_id": offer.pk})

    assert response.status_code == 302
    assert response.url == reverse("cart:detail")
    assert CartItem.objects.filter(cart__owner=user, offer=offer).exists()


@pytest.mark.django_db
def test_adding_the_same_offer_twice_keeps_one_item_and_shows_distinct_messages(
    client,
):
    user = get_user_model().objects.create_user(
        username="repeated-offer-user",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    client.force_login(user)

    first_response = client.post(
        reverse("cart:add-item"),
        {"offer_id": offer.pk},
        follow=True,
    )
    second_response = client.post(
        reverse("cart:add-item"),
        {"offer_id": offer.pk},
        follow=True,
    )

    assert first_response.redirect_chain == [(reverse("cart:detail"), 302)]
    assert "Oferta añadida al carrito." in first_response.content.decode()
    assert second_response.redirect_chain == [(reverse("cart:detail"), 302)]
    assert "La oferta ya estaba en tu carrito." in second_response.content.decode()
    assert CartItem.objects.filter(cart__owner=user, offer=offer).count() == 1


@pytest.mark.django_db
def test_cart_shows_two_items_for_different_license_offers_of_the_same_product(
    client,
):
    user = get_user_model().objects.create_user(
        username="different-license-cart-user",
        password="ReliablePassword123!",
    )
    first_offer = create_available_offer()
    second_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
    )
    second_offer = ProductLicenseOffer.objects.create(
        product=first_offer.product,
        license_type=second_license_type,
        price=Decimal("29.90"),
    )
    client.force_login(user)

    client.post(reverse("cart:add-item"), {"offer_id": first_offer.pk})
    client.post(reverse("cart:add-item"), {"offer_id": second_offer.pk})
    response = client.get(reverse("cart:detail"))
    content = response.content.decode()

    assert response.status_code == 200
    assert first_offer.license_type.name in content
    assert second_offer.license_type.name in content


@pytest.mark.django_db
def test_cart_shows_available_offer_details_and_decimal_total(client):
    user = get_user_model().objects.create_user(
        username="cart-summary-user",
        password="ReliablePassword123!",
    )
    first_offer = create_available_offer()
    second_license_type = LicenseType.objects.create(
        name="Publicidad comercial",
        slug="publicidad-comercial",
        usage_scope="Una campaña publicitaria",
        summary="Uso en una campaña de publicidad comercial.",
        terms_version="1.0",
    )
    second_offer = ProductLicenseOffer.objects.create(
        product=first_offer.product,
        license_type=second_license_type,
        price=Decimal("7.10"),
    )
    client.force_login(user)

    client.post(reverse("cart:add-item"), {"offer_id": first_offer.pk})
    client.post(reverse("cart:add-item"), {"offer_id": second_offer.pk})
    response = client.get(reverse("cart:detail"))
    content = response.content.decode()

    assert response.status_code == 200
    assert first_offer.product.name in content
    assert first_offer.license_type.name in content
    assert first_offer.license_type.usage_scope in content
    assert "12,90 EUR" in content
    assert second_offer.license_type.name in content
    assert second_offer.license_type.usage_scope in content
    assert "7,10 EUR" in content
    assert "20,00 EUR" in content


@pytest.mark.django_db
def test_cart_with_items_shows_a_csrf_protected_order_creation_form(client):
    user = get_user_model().objects.create_user(
        username="cart-order-creation-user",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    client.force_login(user)
    client.post(reverse("cart:add-item"), {"offer_id": offer.pk})

    response = client.get(reverse("cart:detail"))
    content = response.content.decode()

    assert response.status_code == 200
    assert f'action="{reverse("orders:create")}"' in content
    assert 'method="post"' in content
    assert "csrfmiddlewaretoken" in content
    assert "Crear pedido" in content


@pytest.mark.django_db
def test_cart_shows_unavailable_item_excluded_from_total_and_removable(client):
    user = get_user_model().objects.create_user(
        username="unavailable-cart-item-user",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    client.force_login(user)
    client.post(reverse("cart:add-item"), {"offer_id": offer.pk})
    item = CartItem.objects.get(cart__owner=user, offer=offer)
    offer.is_active = False
    offer.save(update_fields=["is_active"])

    response = client.get(reverse("cart:detail"))
    content = response.content.decode()

    assert response.status_code == 200
    assert offer.product.name in content
    assert "No disponible" in content
    assert "0,00 EUR" in content
    assert reverse("cart:remove-item", args=[item.pk]) in content


@pytest.mark.django_db
@pytest.mark.parametrize("post_data", [{}, {"offer_id": "not-an-id"}])
def test_adding_an_offer_requires_a_valid_offer_id(client, post_data):
    user = get_user_model().objects.create_user(
        username="invalid-offer-id-user",
        password="ReliablePassword123!",
    )
    client.force_login(user)

    response = client.post(reverse("cart:add-item"), post_data)

    assert response.status_code == 400
    assert not Cart.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_adding_an_unavailable_offer_returns_404_without_creating_a_cart(client):
    user = get_user_model().objects.create_user(
        username="unavailable-offer-user",
        password="ReliablePassword123!",
    )
    client.force_login(user)

    response = client.post(reverse("cart:add-item"), {"offer_id": 999})

    assert response.status_code == 404
    assert not Cart.objects.filter(owner=user).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "unavailable_entity", ["product", "category", "offer", "license"]
)
def test_adding_an_offer_with_an_inactive_catalog_entity_returns_404(
    client,
    unavailable_entity,
):
    user = get_user_model().objects.create_user(
        username=f"inactive-{unavailable_entity}-user",
        password="ReliablePassword123!",
    )
    offer = create_available_offer()
    entities = {
        "product": offer.product,
        "category": offer.product.category,
        "offer": offer,
        "license": offer.license_type,
    }
    entity = entities[unavailable_entity]
    entity.is_active = False
    entity.save(update_fields=["is_active"])
    client.force_login(user)

    response = client.post(reverse("cart:add-item"), {"offer_id": offer.pk})

    assert response.status_code == 404
    assert not Cart.objects.filter(owner=user).exists()
    assert not CartItem.objects.filter(cart__owner=user).exists()


@pytest.mark.django_db
def test_removing_an_own_item_requires_post_and_recalculates_cart_total(client):
    user = get_user_model().objects.create_user(
        username="removing-with-total-user",
        password="ReliablePassword123!",
    )
    remaining_offer = create_available_offer()
    removable_license_type = LicenseType.objects.create(
        name="Licencia para eliminar",
        slug="licencia-para-eliminar",
        usage_scope="Un proyecto audiovisual",
        summary="Uso en un proyecto audiovisual.",
        terms_version="1.0",
    )
    removable_offer = ProductLicenseOffer.objects.create(
        product=remaining_offer.product,
        license_type=removable_license_type,
        price=Decimal("7.10"),
    )
    client.force_login(user)
    client.post(reverse("cart:add-item"), {"offer_id": remaining_offer.pk})
    client.post(reverse("cart:add-item"), {"offer_id": removable_offer.pk})
    removable_item = CartItem.objects.get(cart__owner=user, offer=removable_offer)
    remove_url = reverse("cart:remove-item", args=[removable_item.pk])

    get_response = client.get(remove_url)

    assert get_response.status_code == 405
    assert CartItem.objects.filter(pk=removable_item.pk).exists()

    post_response = client.post(remove_url)
    cart_response = client.get(reverse("cart:detail"))
    content = cart_response.content.decode()

    assert post_response.status_code == 302
    assert not CartItem.objects.filter(pk=removable_item.pk).exists()
    assert cart_response.status_code == 200
    assert remaining_offer.license_type.name in content
    assert removable_offer.license_type.name not in content
    assert "Total: 12,90 EUR" in content


@pytest.mark.django_db
def test_authenticated_user_can_remove_an_item_from_their_cart(client):
    user = get_user_model().objects.create_user(
        username="removing-cart-user",
        password="ReliablePassword123!",
    )
    item, _ = add_offer_to_cart(owner=user, offer_id=create_available_offer().pk)
    client.force_login(user)

    response = client.post(reverse("cart:remove-item", args=[item.pk]))

    assert response.status_code == 302
    assert response.url == reverse("cart:detail")
    assert not CartItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_user_cannot_remove_another_users_cart_item(client):
    owner = get_user_model().objects.create_user(
        username="cart-item-owner",
        password="ReliablePassword123!",
    )
    other_user = get_user_model().objects.create_user(
        username="other-cart-user",
        password="ReliablePassword123!",
    )
    item, _ = add_offer_to_cart(owner=owner, offer_id=create_available_offer().pk)
    client.force_login(other_user)

    response = client.post(reverse("cart:remove-item", args=[item.pk]))

    assert response.status_code == 404
    assert CartItem.objects.filter(pk=item.pk).exists()
