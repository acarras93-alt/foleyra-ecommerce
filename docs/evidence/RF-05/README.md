# Evidencias de RF-05

## Finalidad

Este documento organiza las evidencias de RF-05: gestionar los productos del
carrito privado. Su finalidad no es repetir el desarrollo realizado, sino dejar
una prueba ordenada de que el requisito tiene un comportamiento observable,
criterios comprobables y componentes identificables.

Para la memoria del proyecto, estas evidencias permiten justificar que el
carrito no es solo una pantalla, sino una funcionalidad privada con reglas de
negocio: autenticación, propiedad de los datos, operaciones por `POST`, CSRF,
rechazo de ofertas no disponibles y cálculo del total actual.

## Uso en el documento base

RF-05 puede explicarse en la memoria como el primer recorrido privado del
cliente dentro del ecommerce. A partir del detalle de producto, un cliente
autenticado selecciona una oferta concreta de producto y licencia; el sistema
crea o reutiliza su carrito, evita duplicados, muestra el total comprable y
permite eliminar líneas propias.

Texto utilizable en la memoria:

> RF-05 implementa el carrito privado del cliente. La funcionalidad reutiliza
> las reglas de disponibilidad del catálogo, limita las consultas y
> modificaciones al usuario autenticado, protege las escrituras mediante `POST`
> y CSRF, y conserva el carrito como una selección actual previa a la creación
> del pedido histórico.

## Componentes implicados

| Componente | Responsabilidad |
|---|---|
| `apps.cart.models.Cart` | Mantiene un único carrito abierto por usuario. |
| `apps.cart.models.CartItem` | Representa una oferta concreta dentro del carrito. |
| `apps.cart.services.add_offer_to_cart()` | Añade una oferta disponible sin duplicar líneas. |
| `apps.cart.services.remove_cart_item()` | Elimina una línea comprobando que pertenece al usuario. |
| `apps.cart.selectors.get_cart_summary()` | Construye la vista del carrito y calcula el total actual. |
| `apps.cart.views` | Expone la consulta y las operaciones web protegidas. |
| `apps.catalog.selectors` | Define qué ofertas pueden añadirse al carrito. |

## Recorrido funcional comprobado

1. El visitante consulta el catálogo y abre el detalle de un producto.
2. Si está autenticado, puede añadir una oferta concreta al carrito.
3. El sistema valida que la oferta, el producto, la categoría y el tipo de
   licencia siguen activos.
4. El carrito se crea solo cuando hay una escritura válida.
5. Una misma oferta no se duplica en el carrito.
6. Dos licencias distintas para el mismo producto se muestran como líneas
   independientes.
7. El usuario ve producto, licencia, alcance, versión de términos, precio,
   moneda, disponibilidad y total.
8. Una oferta que deja de estar disponible permanece visible, pero se excluye
   del total comprable.
9. El usuario puede eliminar únicamente sus propias líneas mediante `POST`.

## Evidencias recomendadas

| Evidencia | Finalidad |
|---|---|
| `carrito-vacio.png` | Mostrar que un cliente autenticado sin líneas ve un estado vacío. |
| `carrito-con-ofertas.png` | Mostrar producto, licencia, precio, moneda y total del carrito. |
| `oferta-no-disponible.png` | Mostrar que una línea no disponible queda identificada y no forma parte del total. |
| `quality-gate-2026-09-21.md` | Registrar pruebas y controles de calidad ejecutados para cerrar el requisito. |

Si las capturas ya se realizaron fuera del repositorio, este índice permite
citarlas en la memoria sin repetir el proceso. Si se incorporan al repositorio,
deben evitar mostrar datos personales, secretos o información irrelevante del
entorno local.

## Pruebas relacionadas

Las pruebas automatizadas asociadas al requisito se encuentran en:

- `apps/cart/tests/test_models.py`
- `apps/cart/tests/test_services.py`
- `apps/cart/tests/test_views.py`

Cubren acceso privado, CSRF, alta de ofertas, duplicados, ofertas no
disponibles, cálculo del total, eliminación de líneas y aislamiento entre
usuarios.

## Relación con otros requisitos

- RF-01 y RF-02 aportan el catálogo y el detalle desde donde se seleccionan las
  ofertas.
- RF-04 aporta autenticación web.
- RF-06 consume el carrito y lo convierte en un pedido histórico.
- RF-13 queda como futura equivalencia mediante API privada.

## Limitaciones y alcance pendiente

RF-05 no crea pedidos, no reserva precios, no procesa pagos y no concede
licencias adquiridas. El carrito representa una selección actual; la
instantánea histórica se crea después, en RF-06.

El requisito queda documentalmente más fuerte cuando se adjuntan las capturas o
se registra la puerta de calidad final del incremento.