from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


def create_offer():
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


@pytest.mark.django_db
def test_user_can_have_only_one_cart():
    user = get_user_model().objects.create_user(
        username="cart-owner",
        password="ReliablePassword123!",
    )
    Cart.objects.create(owner=user)

    with pytest.raises(IntegrityError):
        Cart.objects.create(owner=user)


@pytest.mark.django_db
def test_cart_cannot_contain_the_same_offer_twice():
    user = get_user_model().objects.create_user(
        username="cart-item-owner",
        password="ReliablePassword123!",
    )
    cart = Cart.objects.create(owner=user)
    offer = create_offer()
    CartItem.objects.create(cart=cart, offer=offer)

    with pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, offer=offer)


@pytest.mark.django_db
def test_deleting_a_cart_deletes_its_items():
    user = get_user_model().objects.create_user(
        username="deleting-cart-owner",
        password="ReliablePassword123!",
    )
    cart = Cart.objects.create(owner=user)
    item = CartItem.objects.create(cart=cart, offer=create_offer())

    cart.delete()

    assert not CartItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_offer_with_cart_items_cannot_be_deleted():
    user = get_user_model().objects.create_user(
        username="protected-offer-owner",
        password="ReliablePassword123!",
    )
    cart = Cart.objects.create(owner=user)
    offer = create_offer()
    CartItem.objects.create(cart=cart, offer=offer)

    with pytest.raises(ProtectedError):
        offer.delete()
