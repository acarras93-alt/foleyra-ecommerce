# RF-10 — Evidencia de implementación parcial

Revisión: **2026-10-11**. Base anterior: `6a0a27c`; incremento local preparado
para versionado y publicación por solicitud del desarrollador.

RF-10 no se declara completo ni `Verificado`. Esta evidencia distingue las
garantías implementadas de las partes todavía pendientes del contrato.

## Comportamiento disponible

- Una aprobación simulada emite un `LicenseGrant` activo por línea dentro de
  la transacción del intento y del estado del pedido. Repeticiones y carreras
  del mismo pedido conservan un único permiso por línea.
- Un fallo durante la emisión revierte intento, estado y permisos creados.
- `/licenses/` muestra permisos propios activos de pedidos pagados, con orden
  por emisión e ID descendentes y estado vacío. La navegación incluye el enlace.
- `/licenses/{license_id}/` muestra datos y condiciones históricas de una
  línea propia, con enlace al pedido y sin rutas del maestro. Anónimos requieren
  login; permisos ajenos e inexistentes reciben un 404 uniforme.
- Las consultas rechazan escrituras y no modifican pedidos, líneas, intentos,
  carrito ni permisos. El listado no aumenta sus consultas entre uno y cinco
  permisos, comprobando también que los cinco se muestran.
- Checkout captura texto, versión, alcance, concedente y titular declarado,
  además de `source_product`. Los datos capturados permanecen independientes
  de los cambios posteriores del catálogo.
- Las líneas antiguas sin condiciones o referencia muestran avisos; consultar
  no reconstruye las asociaciones ni utiliza términos actuales como históricos.

## Trazabilidad del alcance probado

Las pruebas están en `apps/orders/tests/test_services.py` y
`apps/orders/tests/test_views.py`. Los nombres siguientes permiten localizarlas
y ejecutarlas sin duplicar escenarios.

| Parte de RF-10 | Pruebas principales |
|---|---|
| CA01: emisión y replay | `test_approved_payment_issues_one_permission_per_order_item`, `test_payment_replay_with_same_key_preserves_existing_license_grants` |
| CA02: exclusión de compras no pagadas | `test_license_list_excludes_unpaid_order_items` |
| CA03: rollback y carreras del mismo pedido | `test_license_issue_failure_rolls_back_payment_order_and_grants`, `test_concurrent_approvals_issue_exactly_one_grant_per_order_item` |
| CA04–05: vacío, campos, propietarios y orden | `test_authenticated_user_without_grants_sees_empty_license_list`, `test_license_list_shows_only_own_grants_with_fields_in_defined_order` |
| CA06: detalle histórico y privacidad | `test_license_detail_preserves_captured_conditions_after_catalog_changes`, `test_license_detail_does_not_expose_master_paths`, `test_legacy_license_detail_warns_without_using_current_conditions` |
| CA07–08: acceso, métodos y navegación | `test_license_access_redirects_anonymous_users_to_login`, `test_license_access_hides_foreign_and_missing_grants`, `test_license_queries_reject_writes_without_changing_grants`, `test_authenticated_user_can_navigate_to_own_license_detail` |
| CA09: N+1 y ausencia de efectos | `test_license_list_query_count_does_not_grow_with_grants`, `test_license_read_does_not_change_business_data` |
| CA11: referencia al producto y líneas antiguas | `test_cart_conversion_preserves_product_reference_after_sku_changes`, `test_unmapped_order_item_remains_readable_and_pending_delivery` |
| Captura de CA13 y partes de CA14/15 | Las pruebas del detalle histórico y la fixture `documented_purchase` recorren la captura, pago y lectura; esto no cubre las validaciones ni regularizaciones pendientes |

Implementación: modelos/servicio/vistas de `apps.orders`, modelos de
`apps.catalog`, rutas de `config/urls.py`, templates de licencias/pedido y
navegación de `templates/base.html`.

## Migraciones incluidas

- `catalog.0003_licensetype_terms_text_and_more`.
- `orders.0006_licensegrant`.
- `orders.0007_orderitem_grantor_name_orderitem_rights_holder_name_and_more`.
- `orders.0008_orderitem_source_product`.

Se revisaron los archivos y se comprobó que ya estaban aplicados en la base
local. Esta revisión no creó ni aplicó migraciones sobre los datos de desarrollo.
Pytest prepara su propia base PostgreSQL con las migraciones versionadas.

## Resultados y reproducción

La [puerta de calidad](quality-gate-2026-10-11.md) registra **30 pruebas
seleccionadas satisfactorias** y **250 pruebas satisfactorias** en la batería
completa, junto con los controles estáticos y de migraciones.

La prueba `test_order_preserves_license_conditions_after_catalog_changes` de
servicios contiene únicamente `pass`: pytest la contabiliza, pero no demuestra
una garantía y no se usa en esta matriz. La preservación del detalle tiene una
prueba real independiente; las operaciones pendientes no se dan por cubiertas.

## Pendientes y límites

- CA10: regularización explícita e idempotente de permisos de compras antiguas.
- CA11 ampliado: referencia estable al tipo de licencia; solo existe
  `source_product`, no `source_license_type`.
- CA12: prevención de recompra e integración con carrito, checkout y pagos,
  incluidas carreras entre pedidos diferentes.
- CA14: rechazo de modificaciones de contenido que mantengan la misma versión.
- CA15: regularización explícita y revisada de condiciones antiguas.
- CA16: consulta previa completa y rechazo de checkout/aprobación con
  condiciones o identidades declaradas incompletas.
- RF-11: vínculo al archivo maestro histórico y descarga autorizada.
- RF-13/14: API privada; RF-15: administración de catálogo y compras.
- Capturas y revisión visual manual, instalación limpia y validación de extremo
  a extremo con productos sonoros reales.

Una batería Green no sustituye la implementación de esos contratos. No se
atribuyen un Red anterior, una instalación limpia ni evidencias visuales que
no se han realizado en esta revisión. El commit de este incremento se localiza
con `git log -1 -- docs/evidence/RF-10/README.md`.
