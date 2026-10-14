# RF-10 — Permisos de uso y condiciones históricas verificados

## Estado y alcance

RF-10 queda **Verificado el 2026-10-14**, por solicitud expresa del desarrollador,
para el contrato HTTP/HTML, los servicios de negocio y la persistencia comprobada
con PostgreSQL. La batería final obtiene **322 pruebas superadas**. Los comandos,
resultados y procedencia de la evidencia están en la
[puerta de calidad](quality-gate-2026-10-14.md).

La [puerta del 2026-10-11](quality-gate-2026-10-11.md) conserva el resultado
histórico de la implementación parcial. Sus 250 pruebas y sus pendientes no
representan el estado actual. El commit anterior de esa publicación es `be94cb1`.

## Comportamiento disponible

- La aprobación de un pedido propio registra el intento, el estado pagado y un
  permiso activo por línea en una transacción. Un fallo de emisión revierte todo.
- El replay conserva el resultado original. Los pagos del mismo propietario
  bloquean primero su fila y después el pedido; dos pedidos concurrentes no
  adquieren dos veces la misma combinación por este servicio.
- La identidad comprada utiliza `source_product` y `source_license_type`.
  Nombres, SKU, precio, moneda o versión no permiten eludir el bloqueo de recompra.
- Una posible coincidencia con un permiso antiguo sin referencias recibe 409.
  Las referencias conocidas se usan para descartar combinaciones diferentes;
  no se adivinan identidades por nombres o SKU. Una nueva aprobación con líneas
  propias sin identificar también se rechaza antes de registrar el intento.
- Checkout captura versión, texto, alcance, concedente y titular declarado del
  servidor. Checkout y aprobación rechazan campos vacíos o compuestos solo por
  espacios. La aprobación usa los datos históricos, no el catálogo actual.
- La página pública del producto muestra las condiciones y la versión antes de
  comprar. `LicenseType.save()` rechaza cambios de texto/alcance sin nueva versión,
  teniendo en cuenta qué campos se guardan mediante `update_fields`.
- `/licenses/` y `/licenses/{license_id}/` son consultas propias: login para
  anónimos, 404 para identificadores ajenos/inexistentes y 405 para escrituras.
  Muestran datos históricos, enlaces de navegación y avisos de documentación
  ausente, sin exponer archivos maestros ni crear/modificar datos de negocio.
- Listado y detalle mantienen el número de consultas cuando el propietario pasa
  de uno a cinco permisos. Las relaciones necesarias se cargan de forma conjunta.

## Matriz de trazabilidad CA01–CA16

Las pruebas viven en [test_services.py](../../../apps/orders/tests/test_services.py)
y [test_views.py](../../../apps/orders/tests/test_views.py). Los nombres permiten
seleccionar cada comportamiento con pytest, sin presentar la mera recogida de
casos como una ejecución satisfactoria.

| Criterio | Pruebas principales | Garantía comprobada |
|---|---|---|
| CA01 | `test_approved_payment_issues_one_permission_per_order_item`, `test_payment_replay_with_same_key_preserves_existing_license_grants` | Un permiso activo por línea, propietario correcto y replay sin duplicados. |
| CA02 | `test_license_list_excludes_unpaid_order_items` | Los pedidos pendientes sin intentos o con intento fallido no aparecen como derechos; existe una compra pagada de control. |
| CA03 | `test_license_issue_failure_rolls_back_payment_order_and_grants`, `test_concurrent_approvals_issue_exactly_one_grant_per_order_item` | Fallar en la segunda emisión revierte pedido, intento y primer permiso; la carrera del mismo pedido conserva una emisión por línea. |
| CA04 | `test_authenticated_user_without_grants_sees_empty_license_list` | Consulta vacía con 200 y sin crear derechos. |
| CA05 | `test_license_list_shows_only_own_grants_with_fields_in_defined_order` | Campos, aislamiento por propietario y orden de emisión/identificador. |
| CA06 | `test_license_detail_preserves_captured_conditions_after_catalog_changes`, `test_license_detail_does_not_expose_master_paths`, `test_legacy_license_detail_warns_without_using_current_conditions` | Detalle histórico, enlace al pedido propio, privacidad del maestro y aviso sin sustituir términos antiguos por actuales. |
| CA07 | `test_license_access_redirects_anonymous_users_to_login`, `test_license_access_hides_foreign_and_missing_grants`, `test_license_queries_reject_writes_without_changing_grants` | Login, 404 uniforme y rechazo de escrituras sin efectos. |
| CA08 | `test_authenticated_user_can_navigate_to_own_license_detail` | Enlace a Mis licencias y al detalle propio, accesibles por GET. |
| CA09 | `test_license_list_query_count_does_not_grow_with_grants`, `test_license_detail_query_count_does_not_grow_with_owned_grants`, `test_license_read_does_not_change_business_data` | Consultas constantes con uno/cinco permisos; pedidos, líneas, intentos, carrito y derechos sin cambios por lectura. |
| CA10 | `test_regularization_creates_only_missing_grants_for_paid_orders` | Solo permisos faltantes de pedidos pagados seleccionados; conservación de existentes y datos históricos, exclusión de pendientes y repetición sin cambios. |
| CA11 | `test_cart_conversion_preserves_product_reference_after_sku_changes`, `test_unmapped_order_item_remains_readable_and_pending_delivery` | Referencias técnicas estables de producto/tipo, snapshots conservados y lectura de líneas antiguas sin mapeo. |
| CA12 | `test_rf10_repurchase_is_rejected_without_business_changes`, `test_rf10_repurchase_rule_allows_distinct_acquisitions`, `test_rf10_original_payment_replay_preserves_success`, `test_rf10_concurrent_orders_cannot_acquire_same_combination_twice`, `test_unresolved_previous_purchase_blocks_possible_repurchase`, `test_payment_rejects_pending_order_with_unresolved_identity` | Recompra rechazada en carrito/checkout/pago, variaciones comerciales, combinaciones/clientes distintos, replay, carrera entre pedidos y rechazo de identidades sin resolver. |
| CA13 | `test_cart_conversion_preserves_product_reference_after_sku_changes`, `test_rf10_pending_order_preserves_conditions_through_payment`, `test_license_detail_preserves_captured_conditions_after_catalog_changes` | Captura de los campos del servidor y lectura de los mismos datos tras pagar y cambiar el catálogo. |
| CA14 | `test_rf10_license_content_change_requires_new_version`, `test_rf10_pending_order_preserves_conditions_through_payment`, `test_license_detail_preserves_captured_conditions_after_catalog_changes` | Rechazo de cambio de texto/alcance con igual versión y conservación de condiciones pendientes/pagadas ante nueva versión. |
| CA15 | `test_legacy_license_detail_warns_without_using_current_conditions`, `test_legacy_documentation_fills_missing_data_and_preserves_snapshots`, `test_legacy_documentation_rejects_invalid_mapping_without_changes` | Aviso, documentación revisada, conservación, idempotencia y siete rechazos: ausencia, ambigüedad, otra línea, revisión inválida, versión/alcance/referencia incompatibles. |
| CA16 | `test_rf10_customer_can_read_conditions_before_creating_order`, `test_rf10_incomplete_conditions_reject_operation_without_changes` | Texto/versión antes de comprar; veinte casos de checkout/pago con cinco campos vacíos o con espacios, 409 y ningún cambio parcial. |

## Operaciones explícitas para compras antiguas

Las funciones están en [services.py](../../../apps/orders/services.py). Son
operaciones internas para una sesión administrativa controlada; los GET no las
invocan y no se añade un endpoint público de escritura.

1. `regularize_paid_order_grants(order_ids=...)` recibe una selección explícita,
   excluye pedidos pendientes y devuelve cuántos permisos ha creado. Conserva
   los existentes mediante `get_or_create` y la unicidad de `order_item`. No
   vuelve a pagar ni completa documentación desconocida.
2. `regularize_legacy_order_item(order_item_id=..., mappings=...)` recibe una
   única correspondencia revisada para esa línea, referencias técnicas existentes,
   condiciones históricas completas, referencia de evidencia, administrador
   activo revisor y fecha válida. Comprueba todas las incompatibilidades antes de
   guardar únicamente los campos vacíos. Una repetición idéntica no escribe.

El operador debe revisar la procedencia histórica fuera de la aplicación y
conservar su respaldo. Los metadatos de revisión se validan como entrada, pero
no se persisten como auditoría ni autentican al ejecutor. Una identidad de revisor
no es una firma ni una constancia de aceptación del cliente. La interfaz y los
permisos administrativos de RF-15 siguen pendientes. Antes de poner compras
antiguas en el recorrido actual, el operador debe regularizar sus permisos
faltantes; la prevención de recompra consulta los derechos activos registrados.

## Cambios y migraciones del incremento

- `orders.0009_orderitem_source_license_type`: FK protegida y nullable para datos
  antiguos, sin inventar correspondencias ni sobrescribir snapshots.
- Reglas en `apps/orders/policies.py`, utilizadas por carrito y pedidos, con
  traducción a HTTP 409 en las vistas.
- Bloqueo por propietario en aprobación y regularizaciones, dentro de transacciones.
- Versionado en el modelo de catálogo y texto/versión en el detalle público.
- Preparaciones de pruebas válidas actualizadas para incluir documentación y
  referencias. Las compras antiguas/incompletas deliberadas mantienen su escenario.
  La prueba de tres líneas conserva precios individuales y corrige el total a 31,30 EUR.

Las migraciones anteriores siguen aplicadas hasta `catalog.0003`; `orders.0009`
ya estaba aplicada durante la revisión. No se ejecutó `migrate` sobre desarrollo.

## Límites de la verificación

- Verificación automatizada de HTTP/HTML, servicios y PostgreSQL con datos
  sintéticos; no acredita revisión visual, instalación limpia, sonidos reales
  ni despliegue en producción.
- Las carreras usan conexiones independientes y verifican sus resultados; no
  enumeran todos los intercalados posibles. El bloqueo serializa los pagos de
  un mismo cliente, incluidas combinaciones diferentes.
- El versionado se comprueba por `save()`. `QuerySet.update()`, SQL y otras
  escrituras que lo omitan no constituyen un flujo permitido de edición de
  condiciones. La presentación de errores y los permisos de Admin son RF-15.
- Las referencias conocidas que distinguen compras incompletas se revisaron en
  la regla; los casos automatizados de compra permitida cubren otros clientes y
  combinaciones con referencias completas. No se atribuyen casos adicionales.
- Descarga y vínculo al maestro, API privada, Admin, PDF, firma y auditoría
  documental persistente no quedan certificados por este cierre.
- La reorganización de los archivos grandes de pruebas queda como tarea separada.

El commit reúne el trabajo del desarrollador y esta revisión de cierre. Su
identificador se obtiene con `git log -1 -- docs/evidence/RF-10/README.md`.
No se realiza push como parte de esta solicitud.
