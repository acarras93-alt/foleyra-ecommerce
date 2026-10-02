# Evidencias de RF-07 — Pago simulado aprobado

## Estado y alcance

RF-07 queda Verificado el 2026-10-02 para el alcance de aprobación simulada por
web, pago independiente del checkout y conservación del historial y carrito.
La verificación utiliza pruebas de integración HTTP/HTML contra PostgreSQL.
No se afirma una comprobación visual manual ni se generan capturas de navegador.
La solicitud del desarrollador autoriza el cierre documental y su commit.

`POST /orders/{order_id}/payments/simulate/` admite result=approved y un UUID.
El formulario incluye CSRF. La operación solo accede a un pedido propio:
ajeno o inexistente obtiene un 404 uniforme, también con campos extra. Sobre
pedidos propios, campos extra o datos inválidos obtienen 400. Una clave nueva
sobre un pedido pagado obtiene 409; un replay compatible conserva el éxito.

Order y PaymentAttempt se guardan dentro de la misma transacción, bloqueando
el pedido. Los datos monetarios proceden del pedido histórico. No se cobran
importes reales ni se crean derechos. RF-08, RF-10 y RF-14 desarrollarán rechazo
y reintento, emisión de derechos y API privada respectivamente.

## Trazabilidad de criterios

Todas estas pruebas se encuentran en `apps/orders/tests/test_views.py`.

| Criterio | Prueba | Evidencia observable |
|---|---|---|
| CA-RF07-01 | `test_pending_order_detail_shows_payment_form_without_business_changues` | Formulario POST al pedido, CSRF, UUID y result=approved; GET conserva pedidos, líneas, intentos y carrito. |
| CA-RF07-02 | `test_payment_simulation_rejects_unauthorized_requests_without_business_changes` | Tres casos: anónimo con CSRF obtiene login y next interno; sin CSRF obtiene 403; GET obtiene 405. Pedidos e intentos intactos. |
| CA-RF07-03 | `test_payment_simulation_returns_same_404_for_foreing_and_missing_orders` | Seis casos: entrada válida o extras owner, amount, currency, status y desconocido. Cada caso comprueba 404 idéntico para ajeno e inexistente, ausencia de datos privados y conservación de pedidos, líneas, intentos y carrito. |
| CA-RF07-04 | `test_owner_can_approve_simulated_payment_for_pending_order` | Un intento aprobado, fecha, clave e importe; estado paid, redirección, mensaje, líneas y datos históricos. |
| CA-RF07-05 | `test_payment_preserves_order_amount_and_currency_after_offer_changes`, `test_payment_preserves_cart_content_added_after_order_creation`, `test_payment_rejects_extra_business_fields_without_changes` | Precio y moneda históricos tras cambiar la oferta; carrito posterior intacto; cuatro campos monetarios/de propiedad/estado rechazados con 400 sin cambios. |
| CA-RF07-06 | `test_paid_order_rejects_new_payment_key_without_second_approval`, `test_payment_replay_with_same_key_preserves_original_approval` | Nueva clave obtiene 409; replay obtiene la misma redirección y conserva un único intento original. |
| CA-RF07-07 | `test_concurrent_payments_preserve_single_approval` | Dos casos y dos backend PID PostgreSQL distintos: misma clave obtiene 302/302; distintas obtienen 302/409. Un único intento, estado e historia coherentes. |
| CA-RF07-08 | `test_payment_failure_rolls_back_attempt_and_preserves_cart` | Fallo técnico después de insertar intento y antes de guardar paid; reversión completa de pedido e intento, líneas y carrito intactos. |
| CA-RF07-09 | `test_payment_rejects_invalid_input_without_business_changes` | Seis casos de resultados/UUID inválidos, vacíos o ausentes; 400 sin cambios, traceback, SECRET_KEY ni ruta de proyecto. |

La selección reúne 28 casos parametrizados. La inexistencia actual de modelos
de derechos se declara como límite de alcance, no como prueba de una emisión.

## Ciclo de comprobación

La implementación ya existía al comenzar la revisión y su primera ejecución
completa pasó con PostgreSQL; no se reconstruye un RED de desarrollo inicial.
El fallo de prioridad de propiedad sí se reprodujo antes de corregirlo:
5 failed y 5 passed. Tras corregirlo, esa selección obtuvo 10 passed.

Al cerrar la evidencia se completaron las instantáneas de intentos en GET y
peticiones no autorizadas y se limpiaron espacios de la plantilla; los 28 casos
del requisito pasan. Véase la [puerta de calidad](quality-gate-2026-10-02.md).

## Código y commit

Modelo: `apps/orders/models.py`. Migración:
`apps/orders/migrations/0004_alter_order_status_paymentattempt.py`.
Servicio: `approve_simulated_payment` en `apps/orders/services.py`.
Vista, URL y plantilla: `apps/orders/views.py`, `apps/orders/urls.py` y
`apps/orders/templates/orders/order_detail.html`.

El commit incluye implementación, corrección, pruebas y evidencias; puede
identificarse con `git log -1 -- docs/evidence/RF-07/README.md`.
Las pruebas usan una base independiente creada por pytest-django y no pagos de
clientes reales. No se incluyen secretos, credenciales ni el archivo .env.
