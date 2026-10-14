from django.db.models import Q

from apps.orders.models import LicenseGrant


class LicenseAlreadyOwned(Exception):
    """El cliente ya tiene un permiso activo para esta combinación."""


class IncompleteLicenseConditions(Exception):
    """Faltan condiciones o identidades necesarias para completar la compra."""


class UnresolvedLicenseIdentity(Exception):
    """Una compra anterior podría corresponder a la combinación solicitada."""


def ensure_complete_license_conditions(
    *,
    terms_version,
    terms_text,
    usage_scope,
    grantor_name,
    rights_holder_name,
):
    values = (
        terms_version,
        terms_text,
        usage_scope,
        grantor_name,
        rights_holder_name,
    )

    if not all(value.strip() for value in values):
        raise IncompleteLicenseConditions(
            "No se puede completar la compra: "
            "las condiciones de uso o las identidades declaradas están incompletas."
        )


def ensure_license_not_owned(*, owner, product, license_type):
    own_grants = LicenseGrant.objects.filter(
        order_item__order__owner=owner,
        status=LicenseGrant.Status.ACTIVE,
    )

    # Rechazar una coincidencia confirmada mediante ambas referencias.
    already_owned = own_grants.filter(
        order_item__source_product=product,
        order_item__source_license_type=license_type,
    ).exists()

    if already_owned:
        raise LicenseAlreadyOwned(
            "Ya tienes un permiso activo para este producto y tipo de licencia."
        )

    # Buscar identidades incompletas que podrían ser la misma combinación.
    unresolved_match = (
        own_grants.filter(
            Q(order_item__source_product__isnull=True)
            | Q(order_item__source_license_type__isnull=True),
        )
        .filter(
            Q(order_item__source_product=product)
            | Q(order_item__source_product__isnull=True),
        )
        .filter(
            Q(order_item__source_license_type=license_type)
            | Q(order_item__source_license_type__isnull=True),
        )
        .exists()
    )

    if unresolved_match:
        raise UnresolvedLicenseIdentity(
            "Una compra anterior necesita revisión antes de adquirir esta licencia."
        )
