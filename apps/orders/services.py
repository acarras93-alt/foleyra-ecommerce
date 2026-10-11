from decimal import Decimal
from uuid import UUID

from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.selectors import is_offer_available
from apps.orders.models import LicenseGrant, Order, OrderItem, PaymentAttempt


class EmptyCart(Exception):
    pass


class OfferNotAvailable(Exception):
    pass


class InvalidPaymentInput(Exception):
    pass


class PaymentConflict(Exception):
    pass


@transaction.atomic
def create_order_from_cart(*, owner) -> Order:
    try:
        cart = Cart.objects.select_for_update().get(owner=owner)
    except Cart.DoesNotExist:
        raise EmptyCart from None
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart)
        .select_related("offer__product__category", "offer__license_type")
    )
    if not cart_items:
        raise EmptyCart
    if any(not is_offer_available(item.offer) for item in cart_items):
        raise OfferNotAvailable
    total_amount = sum((item.offer.price for item in cart_items), Decimal("0.00"))
    order = Order.objects.create(
        owner=owner,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=total_amount,
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                source_product=item.offer.product,
                product_sku=item.offer.product.sku,
                product_name=item.offer.product.name,
                license_name=item.offer.license_type.name,
                terms_version=item.offer.license_type.terms_version,
                terms_text=item.offer.license_type.terms_text,
                usage_scope=item.offer.license_type.usage_scope,
                grantor_name=item.offer.grantor_name,
                rights_holder_name=item.offer.rights_holder_name,
                price=item.offer.price,
                currency=item.offer.currency,
            )
            for item in cart_items
        ]
    )
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def approve_simulated_payment(
    *,
    owner,
    order_id,
    result,
    idempotency_key,
) -> PaymentAttempt:
    # Obtener y bloquear únicamente el pedido del propietario.
    order = Order.objects.select_for_update().get(
        pk=order_id,
        owner=owner,
    )

    # Admitir aprobación y rechazo simulados.
    if result not in (
        PaymentAttempt.Result.APPROVED,
        PaymentAttempt.Result.FAILED,
    ):
        raise InvalidPaymentInput

    try:
        payment_key = UUID(str(idempotency_key))
    except ValueError:
        raise InvalidPaymentInput from None

    previous_attempt = PaymentAttempt.objects.filter(
        order=order, idempotency_key=payment_key
    ).first()

    # Si ya existe ese intento con el mismo resultado, devolverlo sin escribir nada.
    if previous_attempt is not None:
        if previous_attempt.result != result:
            raise PaymentConflict
        return previous_attempt

    # Una clave nueva solo puede utilizarse en un pedido pendiente.
    if order.status != Order.Status.PENDING_PAYMENT:
        raise PaymentConflict

    # Registrar el resultado con el importe y moneda históricos.
    attempt = PaymentAttempt.objects.create(
        order=order,
        idempotency_key=payment_key,
        result=result,
        amount=order.total_amount,
        currency=order.currency,
    )

    # Marca el pedido como pagado, recupera sus lineas historicas y crea un derecho activo a cada linea.
    if result == PaymentAttempt.Result.APPROVED:
        order.status = Order.Status.PAID
        order.save(update_fields=["status"])

        for order_item in OrderItem.objects.filter(order=order):
            LicenseGrant.objects.create(
                order_item=order_item,
                status=LicenseGrant.Status.ACTIVE,
            )

    return attempt
