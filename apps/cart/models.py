from django.conf import settings
from django.db import models

from apps.catalog.models import ProductLicenseOffer


class Cart(models.Model):
    """Represent a user's temporary selection of offers.

    Each user can have at most one cart.
    """

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )


class CartItem(models.Model):
    """Link an offer to a cart, allowing each offer only once per cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    offer = models.ForeignKey(
        ProductLicenseOffer,
        on_delete=models.PROTECT,
        related_name="cart_items",
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["cart", "offer"],
                name="uniq_cart_offer",
            )
        ]
