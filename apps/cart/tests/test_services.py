from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.cart.models import Cart, CartItem
from apps.cart.selectors import get_cart_summary
from apps.cart.services import (
    CartItemNotFound,
    OfferNotAvailable,
    add_offer_to_cart,
    remove_cart_item,
)
from apps.catalog.models import Category, LicenseType, Product, ProductLicenseOffer


def create_offer(*, number, product=None):
    if product is None:
        category = Category.objects.create(
            name=f"Categoría {number}",
            slug=f"categoria-{number}",
        )
        product = Product.objects.create(
            category=category,
            name=f"Producto {number}",
            slug=f"producto-{number}",
            sku=f"SKU-{number}",
            summary="Producto de prueba.",
            description="Descripción de producto de prueba.",
            duration_ms=18_500,
            audio_format="wav",
            sample_rate_hz=48_000,
            bit_depth=24,
        )
    license_type = LicenseType.objects.create(
        name=f"Licencia {number}",
        slug=f"licencia-{number}",
        usage_scope=f"Alcance {number}",
        summary="Resumen de licencia de prueba.",
        terms_version="1.0",
    )
    return ProductLicenseOffer.objects.create(
        product=product,
        license_type=license_type,
        price=Decimal("12.90"),
    )


def create_user(username):
    return get_user_model().objects.create_user(
        username=username,
        password="ReliablePassword123!",
    )


@pytest.mark.django_db
def test_add_offer_creates_the_owners_cart_and_item():
    user = create_user("cart-service-owner")
    offer = create_offer(number=1)

    item, created = add_offer_to_cart(owner=user, offer_id=offer.pk)

    assert created is True
    assert item.offer == offer
    assert item.cart.owner == user


@pytest.mark.django_db
def test_adding_the_same_offer_twice_keeps_one_item():
    user = create_user("idempotent-owner")
    offer = create_offer(number=2)

    first_item, first_created = add_offer_to_cart(owner=user, offer_id=offer.pk)
    second_item, second_created = add_offer_to_cart(owner=user, offer_id=offer.pk)

    assert first_created is True
    assert second_created is False
    assert second_item == first_item
    assert CartItem.objects.filter(cart__owner=user, offer=offer).count() == 1


@pytest.mark.django_db
def test_adding_two_license_offers_for_the_same_product_creates_two_items():
    user = create_user("different-license-owner")
    first_offer = create_offer(number=8)
    second_offer = create_offer(number=9, product=first_offer.product)

    first_item, first_created = add_offer_to_cart(owner=user, offer_id=first_offer.pk)
    second_item, second_created = add_offer_to_cart(
        owner=user,
        offer_id=second_offer.pk,
    )

    assert first_created is True
    assert second_created is True
    assert first_item.offer.product == second_item.offer.product
    assert first_item.offer.license_type != second_item.offer.license_type
    assert CartItem.objects.filter(cart__owner=user).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "unavailable_entity", ["product", "category", "offer", "license"]
)
def test_add_offer_rejects_every_unavailable_catalog_state(unavailable_entity):
    user = create_user(f"unavailable-{unavailable_entity}")
    offer = create_offer(number=3)
    entities = {
        "product": offer.product,
        "category": offer.product.category,
        "offer": offer,
        "license": offer.license_type,
    }
    entity = entities[unavailable_entity]
    entity.is_active = False
    entity.save(update_fields=["is_active"])

    with pytest.raises(OfferNotAvailable):
        add_offer_to_cart(owner=user, offer_id=offer.pk)

    assert not Cart.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_removing_an_item_is_limited_to_its_owner():
    owner = create_user("item-owner")
    other_user = create_user("other-user")
    offer = create_offer(number=4)
    item, _ = add_offer_to_cart(owner=owner, offer_id=offer.pk)

    with pytest.raises(CartItemNotFound):
        remove_cart_item(owner=other_user, item_id=item.pk)

    assert CartItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_owner_can_remove_an_item():
    owner = create_user("removing-item-owner")
    offer = create_offer(number=7)
    item, _ = add_offer_to_cart(owner=owner, offer_id=offer.pk)

    remove_cart_item(owner=owner, item_id=item.pk)

    assert not CartItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_cart_summary_uses_current_prices_and_excludes_unavailable_items():
    user = create_user("summary-owner")
    first_offer = create_offer(number=5)
    second_offer = create_offer(number=6)
    add_offer_to_cart(owner=user, offer_id=first_offer.pk)
    add_offer_to_cart(owner=user, offer_id=second_offer.pk)
    first_offer.price = Decimal("20.00")
    first_offer.save(update_fields=["price"])
    second_offer.is_active = False
    second_offer.save(update_fields=["is_active"])

    summary = get_cart_summary(owner=user)

    assert summary.total == Decimal("20.00")
    assert [(item.offer_id, item.is_available) for item in summary.items] == [
        (first_offer.pk, True),
        (second_offer.pk, False),
    ]
