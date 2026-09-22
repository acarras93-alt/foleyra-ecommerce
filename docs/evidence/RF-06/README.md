# Evidencias de RF-06

## Finalidad

Este documento organiza las evidencias de RF-06: convertir el carrito en un
pedido histórico. Su objetivo es explicar y demostrar el cambio de fase del
recorrido de compra: el carrito deja de ser una selección editable y pasa a ser
un pedido persistido con datos históricos propios.

Para la memoria del proyecto, estas evidencias justifican que el sistema no
depende del catálogo vivo para recordar una compra iniciada. El pedido conserva
una instantánea de producto, licencia, versión de términos, precio y moneda en
el momento de la conversión.

## Uso en el documento base

RF-06 puede explicarse como el cierre del checkout previo al pago. Un cliente
autenticado convierte su carrito en un pedido en estado `pending_payment`; la
operación se ejecuta de forma atómica, recalcula el total en EUR, crea líneas
históricas y vacía el carrito solo si todo el proceso finaliza correctamente.

Texto utilizable en la memoria:

> RF-06 transforma el carrito privado en un pedido histórico pendiente de pago.
> La operación usa un servicio transaccional, bloquea el carrito durante la
> conversión, revalida la disponibilidad de las ofertas, captura los datos de
> compra y evita pedidos parciales si se produce un error.

## Componentes implicados

| Componente | Responsabilidad |
|---|---|
| `apps.orders.models.Order` | Representa el pedido del cliente y su estado de pago. |
| `apps.orders.models.OrderItem` | Conserva la instantánea histórica de cada línea comprada. |
| `apps.orders.services.create_order_from_cart()` | Convierte el carrito en pedido dentro de una transacción. |
| `apps.orders.views.create_order()` | Expone la operación web mediante `POST`. |
| `apps.cart.models.CartItem` | Proporciona las líneas actuales que serán convertidas. |
| `apps.catalog.selectors.is_offer_available()` | Revalida disponibilidad antes de crear el pedido. |

## Recorrido funcional comprobado

1. El cliente autenticado tiene un carrito con una o más ofertas disponibles.
2. Envía `POST /orders/create/` desde el formulario del carrito.
3. El servicio bloquea el carrito y sus líneas para evitar conversiones
   duplicadas.
4. El sistema comprueba que el carrito no está vacío.
5. El sistema revalida que todas las ofertas siguen disponibles.
6. Se crea un pedido en estado `pending_payment`.
7. Se crean líneas históricas con SKU, nombre de producto, licencia, versión de
   términos, precio y moneda.
8. El total del pedido se calcula con los importes de las líneas convertidas.
9. El carrito se vacía únicamente si el pedido y sus líneas se han creado
   correctamente.

## Evidencias recomendadas

| Evidencia | Finalidad |
|---|---|
| `pedido-creado.png` | Mostrar el resultado visible tras crear un pedido desde el carrito. |
| `carrito-vaciado.png` | Mostrar que el carrito queda vacío después de una conversión correcta. |
| `pedido-conflicto-409.png` | Mostrar el rechazo de carrito vacío u oferta no disponible. |
| `quality-gate-2026-09-21.md` | Registrar pruebas y controles de calidad ejecutados para cerrar el requisito. |

Si las capturas ya existen en el material personal de la memoria, pueden
citarse desde este índice. Si se copian al repositorio, deben revisarse para no
exponer datos personales, rutas innecesarias, secretos ni contenido ajeno al
requisito.

## Pruebas relacionadas

Las pruebas automatizadas asociadas al requisito se encuentran en:

- `apps/orders/tests/test_services.py`
- `apps/orders/tests/test_views.py`
- `apps/cart/tests/test_views.py`

Cubren conversión correcta, instantánea histórica, carrito vacío, oferta no
disponible, rollback ante fallo, aislamiento entre propietarios, concurrencia,
CSRF, método HTTP y autenticación.

## Relación con otros requisitos

- RF-05 proporciona el carrito que se convierte en pedido.
- RF-07 y RF-08 deberán operar sobre pedidos pendientes de pago.
- RF-09 permitirá consultar los pedidos propios.
- RF-10 creará las licencias adquiridas después de un pago aprobado.
- RF-11 permitirá descargar el archivo autorizado cuando exista derecho de uso.

## Limitaciones y alcance pendiente

RF-06 no procesa pagos, no permite consultar el histórico de pedidos desde una
pantalla propia, no concede licencias adquiridas y no autoriza descargas. Es el
paso intermedio que deja un pedido preparado para los requisitos posteriores.

El requisito queda documentalmente más fuerte cuando se adjuntan las capturas o
se registra la puerta de calidad final del incremento.