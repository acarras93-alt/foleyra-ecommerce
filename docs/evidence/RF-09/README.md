# Evidencias de RF-09 — Consulta de pedidos propios

## Estado y alcance

RF-09 queda `Implementado` el 2026-09-26. El cliente autenticado accede a
«Mis pedidos», consulta `/orders/` y abre `/orders/{order_id}/`. El listado
incluye identificador, fecha, estado, total, moneda y enlace al detalle. El
detalle presenta los datos de compra conservados en `Order` y `OrderItem`.

Los anónimos se redirigen al login con un `next` interno. Para usuarios
autenticados, un pedido ajeno o inexistente recibe el mismo 404 genérico con
`DEBUG=False`. Las vistas declaran `require_GET`; no ofrecen transiciones de
estado ni servicios de creación, pago, cancelación o eliminación.

El estado `Implementado` se distingue de `Verificado`: faltan las capturas
visuales y la revisión manual en navegador. No se afirman evidencias de modelos
que todavía no existen.

## Trazabilidad de pruebas

Todas las funciones de esta tabla pertenecen a `apps/orders/tests/test_views.py`.

| Criterio | Prueba | Comportamiento comprobado |
|---|---|---|
| CA-RF09-01 | `test_anonymous_visitor_is_redirected_to_login_when_consulting_orders` | Redirección al login y `next` para listado y detalle. |
| CA-RF09-02 | `test_authenticated_user_without_orders_sees_empty_order_list` | 200 y mensaje de listado vacío. |
| CA-RF09-03 | `test_authenticated_user_sees_own_order_fields_in_list` y prueba de CA-RF09-04 | Identificador, estado, importe y moneda propios; también fecha y enlace al detalle del flujo aprobado. |
| CA-RF09-04 | `test_order_list_excludes_other_users_orders` | Aparece el pedido propio y se excluye el ajeno. |
| CA-RF09-05 | `test_authenticated_user_sees_own_order_detail_with_historical_items` | Cabecera del pedido y producto, SKU, licencia, términos, precio y moneda históricos. |
| CA-RF09-06 | `test_order_detail_returns_same_404_for_foreign_and_missing_orders` | 404 con el mismo cuerpo para pedido ajeno e inexistente y ausencia del nombre y SKU privados. |
| CA-RF09-07 | `test_order_detail_preserves_snapshot_after_catalog_changes` | Tras cambiar producto, SKU, licencia, términos y precio del catálogo, aparecen los valores originales y no los nuevos. |
| CA-RF09-08 | `test_order_list_orders_by_creation_date_and_id_descending` | Orden en el HTML por fecha descendente y desempate real por ID; el pedido antiguo tiene el ID mayor. |
| CA-RF09-09 | `test_order_read_does_not_change_business_data` | Dos casos parametrizados; todos los registros y campos de pedidos, líneas y carrito permanecen iguales tras cada GET. |
| CA-RF09-10 | `test_order_detail_query_count_does_not_grow_with_items` | Una y diez líneas se renderizan y requieren el mismo número de consultas, con un máximo de cuatro por GET en la configuración actual. |
| CA-RF09-11 | `test_authenticated_user_sees_orders_link_in_main_navigation` | La página principal autenticada incluye «Mis pedidos» con destino a `/orders/`. |

Los modelos de pagos, licencias adquiridas y descargas autorizadas aún no existen.
La cobertura de CA-RF09-09 sobre esas entidades queda diferida a sus respectivos
incrementos. La prueba actual abarca `Order`, `OrderItem`, `Cart` y `CartItem`;
no confunde `LicenseType` con una licencia adquirida.

## Ciclo de desarrollo

Se trabajó criterio a criterio con revisión de precondiciones, acción, resultado
observable y responsabilidades. Las pruebas de listado vacío, presentación del
pedido y navegación permitieron completar vistas y plantillas. Las consultas
por propietario, orden y precarga ya estaban preparadas en el commit `2817481`;
las comprobaciones que pasaron sin cambios de producción son regresiones sobre
comportamiento existente, no ciclos RED-GREEN propios.

Los errores de importación, comandos o diferencias de guion y raya fueron
correcciones de pruebas o herramientas; no se consideran fallos funcionales.
En la revisión de cierre se amplió la prueba de listado para fecha y enlace al
detalle: falló por fecha ausente y pasó después del cambio de plantilla.

## Evidencia disponible

- [Puerta de calidad del 2026-09-26](quality-gate-2026-09-26.md): 172 pruebas
  superadas y controles de Django, migraciones, Ruff y dependencias.
- Código de pruebas y plantillas versionado junto con este documento.
- Bitácora: entrada del 2026-09-26 en `docs/technical-log.md`.

## Evidencia visual pendiente

Estos archivos están previstos, pero todavía no se han generado:

- `listado-pedidos-vacio.png`.
- `listado-pedidos-propios.png`.
- `detalle-pedido-historico.png`.

La comprobación del enlace en el HTML no sustituye la revisión visual de su
visibilidad y del recorrido principal → listado → detalle en el navegador.

## Trazabilidad del commit

La implementación web, las pruebas y esta documentación se incluyen en el
commit `feat(orders): implement private order history`. Su identificador se
obtiene con `git log -1 -- docs/evidence/RF-09/quality-gate-2026-09-26.md`.
El esquema de datos y los selectores proceden del commit previo `2817481`;
este incremento no añade migraciones ni dependencias.
