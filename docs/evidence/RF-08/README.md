# Evidencias de RF-08 — Rechazo y reintento de pago simulado

## Estado y alcance

RF-08 queda `Verificado` el 2026-10-03, por solicitud expresa del desarrollador,
para el contrato HTTP/HTML y la persistencia de rechazos, reintentos e historial.
La evidencia usa PostgreSQL, pruebas de integración de Django y conexiones
independientes para concurrencia. No acredita una revisión visual manual.

El POST `/orders/{order_id}/payments/simulate/` admite `result=failed` y
`result=approved` con una clave UUID. La propiedad se valida en el servidor y los
valores monetarios se toman del pedido. El rechazo registra un intento fallido,
mantiene `pending_payment` y redirige con `Pago simulado rechazado.`. Aprobar con
una clave nueva conserva el rechazo y añade una aprobación, pasando a `paid`.

Un replay conserva el resultado original, incluso si el pedido se pagó después.
Cambiar el resultado de una clave existente o crear otro intento sobre un pedido
pagado obtiene 409 sin cambios. La consulta propia muestra resultados y fechas
en orden `-created_at, -id`, sin exponer las claves de intentos anteriores.

## Trazabilidad

Las pruebas se encuentran en `apps/orders/tests/test_views.py`. Se reutilizan
las garantías ya existentes de RF-07, sin duplicarlas ni fabricar un Red.

| Criterio | Pruebas | Resultado comprobado |
|---|---|---|
| CA-RF08-01 | `test_rejected_payment_records_failed_attempt_and_keeps_order_pending` | Un intento fallido con clave, importe, moneda y fecha; pedido pendiente; redirección y mensaje visible de rechazo. |
| CA-RF08-02 | `test_rejected_payment_preserves_cart_and_historical_order_items` | Rechazo realmente persistido y conservación del carrito y las líneas históricas. Derechos y descargas aún no existen: véanse los límites. |
| CA-RF08-03 | `test_rejected_payment_identical_repetition`, `test_rejected_payment_key_cannot_be_reused_for_approval` | Repetición idéntica sin duplicados; resultado incompatible con la misma clave obtiene 409 y conserva el original. |
| CA-RF08-04 | `test_approved_retry_with_new_key_preserves_failed_attempt` | Dos intentos, una sola aprobación con clave nueva, pedido pagado e intento fallido intacto. |
| CA-RF08-05 | `test_order_detail_shows_only_own_payment_history_without_changes`, `test_order_detail_query_count_does_not_grow_with_payment_attempts` | Solo historial del pedido propio, ambos resultados y fechas visibles, fecha descendente con desempate por ID, ausencia de claves técnicas históricas y de escrituras; consultas constantes con uno y diez intentos. |
| CA-RF08-06 | `test_paid_order_rejects_new_payment_key_without_second_approval`, `test_paid_order_rejects_failed_attempt_with_new_key_without_changes`, `test_payment_replay_with_same_key_preserves_original_approval`, `test_failed_payment_replay_preserves_paid_order_and_attempts` | Nueva aprobación o rechazo con otra clave obtiene 409; replay de aprobación o rechazo conserva los registros y el pedido pagado. |
| CA-RF08-07 | `test_anonymous_payment_rejection_redirects_to_login_without_changes`, `test_payment_rejection_without_csrf_returns_403_without_changes`, `test_payment_rejection_returns_same_404_for_foreign_and_missing_orders`, `test_payment_retry_enforces_security_without_changes` | Anónimo con CSRF válido: 302 al login con next; sin CSRF: 403; ajeno/inexistente: 404. El reintento cubre cinco escenarios, incluido token inválido. Sin escrituras de negocio. |
| CA-RF08-08 | `test_concurrent_rejection_and_approval_preserve_paid_order`, `test_concurrent_payments_preserve_single_approval`, `test_payment_failure_rolls_back_attempt_and_preserves_cart` | Rechazo/aprobación concurrentes y dos aprobaciones concurrentes conservan una sola aprobación y el pedido pagado; el fallo técnico tras insertar un intento revierte sus efectos sin convertirlo en rechazo. |

La comprobación de eficiencia es complementaria a CA-RF08-05. Se conserva
además la regresión con una y diez líneas: el presupuesto del detalle pasa de
cuatro a cinco consultas porque el historial añade una precarga fija.

## Revisión de cierre

El desarrollador comunica la regresión Green y autoriza actualizar documentación
y crear el commit. La revisión vuelve a ejecutar las 75 pruebas de pedidos y
obtiene Green inicial. Se amplía el caso de historial para cubrir el desempate,
las fechas visibles y ambos resultados; también se eliminan las capturas
redundantes que consultaban varias veces los mismos intentos. Las nuevas
capturas abarcan pedidos e intentos de ambos usuarios.

La ampliación pasa inicialmente: no se cambia código de producción durante
esta revisión. La batería completa final obtiene **219 passed**. Los comandos
y resultados constan en la [puerta de calidad](quality-gate-2026-10-03.md).

Durante el trabajo guiado, las capturas aportadas por el desarrollador mostraron
Red por `failed` aún no admitido y por historial aún no renderizado. También
hubo errores de preparación de pruebas (token CSRF, decorador y expectativas)
que no se presentan como defectos del producto. Estos antecedentes no se
confunden con nuevas ejecuciones realizadas por esta revisión.

## Límites

- RF-10 y RF-11 todavía no implementan derechos adquiridos ni descargas. La
  conservación de carrito e historia está probada; la ausencia de esas entidades
  no se presenta como una prueba de denegación de derechos futuros. Se ampliará
  CA-RF08-02 al integrar dichos módulos.
- El rechazo se verifica mediante POST con `result=failed`. El formulario visible
  actual ofrece aprobación/reintento; no se afirma que exista un botón de rechazo.
- La concurrencia libera dos trabajadores con una barrera y verifica dos PID
  PostgreSQL distintos. Acepta ambos órdenes serializados, pero una ejecución
  no fuerza los dos órdenes; los casos secuenciales CA04 y CA06 los complementan.
- No se afirma verificación visual manual, pasarela real, emisión de derechos,
  API privada ni despliegue. El token inválido es una variante complementaria.
- Las pruebas usan la base de pruebas de pytest-django y datos sintéticos. No se
  incluyen secretos, datos reales de clientes ni el archivo `.env`.

## Código y commit

Modelo, servicio, vista y selector: `apps/orders/`. Plantilla:
`apps/orders/templates/orders/order_detail.html`. Migración:
`apps/orders/migrations/0005_alter_paymentattempt_result.py`.

El commit reúne la implementación realizada por el desarrollador, la migración,
las pruebas y esta documentación. Los cambios previos de otros requisitos y
metodología permanecen fuera. No se publica ningún cambio remoto.

Identificación reproducible:

```bash
git log -1 -- docs/evidence/RF-08/README.md
```
