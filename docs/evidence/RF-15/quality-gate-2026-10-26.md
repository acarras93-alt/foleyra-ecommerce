# Puerta de calidad de RF-15

## Alcance

Esta evidencia cubre CA-RF15-01 a CA-RF15-07 y RN-RF15-01 a RN-RF15-07.
CA-RF15-08 a CA-RF15-12 permanecen propuestas.

## Pruebas administrativas

Comando: .venv/bin/python -m pytest -q apps/users/tests/test_admin.py apps/catalog/tests/test_admin.py apps/orders/tests/test_admin.py
Resultado: 16 passed.

Se verifican acceso y permisos, alta y modificación del catálogo, desactivación
con efecto en web y API, validaciones de licencia, ausencia de secretos,
protección de pedidos históricos, bloqueo de pagos y concesiones genéricas,
carga eficiente de relaciones y registros LogEntry.

## Regresión y controles de calidad

Comando: .venv/bin/python -m pytest -q
Resultado: 434 passed in 48.35s.

Comando: .venv/bin/python manage.py check --database default
Resultado: System check identified no issues.

Comando: .venv/bin/python manage.py makemigrations --check --dry-run
Resultado: No changes detected.

Comando: .venv/bin/python manage.py migrate --check
Resultado: All checks passed.

Comando: .venv/bin/ruff check .
Resultado: All checks passed.

Comando: .venv/bin/ruff format --check .
Resultado: 134 files already formatted.

Comando: .venv/bin/pip check
Resultado: No broken requirements found.

Las capturas visuales previstas para el recorrido manual quedan como evidencia
complementaria; esta puerta acredita la verificación automatizada del alcance
aprobado.
