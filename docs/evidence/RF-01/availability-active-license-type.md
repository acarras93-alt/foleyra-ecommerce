# Evidencia de disponibilidad por tipo de licencia activo

## Regla verificada

Una oferta solo hace público y vendible un producto cuando tanto la oferta como
su `LicenseType` están activos. Las ofertas asociadas a tipos inactivos tampoco
participan en el precio mínimo ni en la colección pública precargada.

Esta es una corrección del selector base de RF-01 y RF-02 previa a RF-03. No se
añadieron parámetros de búsqueda, filtro u ordenación.

## Ciclo test-first

RED:

```bash
.venv/bin/python -m pytest -q \
  apps/catalog/tests/test_selectors.py::test_available_products_require_an_active_license_type
```

Resultado: `1 failed`. `get_available_products()` devolvía un producto cuya
única oferta apuntaba a un tipo de licencia inactivo.

GREEN: el mismo comando finalizó con `1 passed`. La regresión de catálogo
finalizó con `22 passed` y la suite completa con `30 passed`.

## Implementación mínima

`get_available_products()` aplica `license_type__is_active=True` de forma
coherente en:

- el conjunto disponible;
- la anotación `minimum_price`;
- la colección de ofertas públicas precargadas.
