# Verificación automatizada de RF-07 — 2026-10-02

## Alcance comprobado

Aprobación simulada independiente del checkout, permiso de propietario antes
de campos extra, valores históricos, idempotencia, concurrencia y rollback.
El código de RF-07, su migración, corrección y pruebas se versionan con esta
evidencia. La matriz de los nueve criterios está en [README](README.md).

## Fallo reproducido y corrección

Antes de corregir la vista se amplió la prueba de 404 uniforme a campos extra.
La selección de esta prueba y la de campos extra sobre pedidos propios obtuvo
`5 failed, 5 passed, 35 deselected in 5.84s`: los cinco casos de campos extra
recibían 400 sobre pedidos ajenos. Tras comprobar primero la propiedad, la
misma selección obtuvo `10 passed, 35 deselected in 4.24s`. Cada caso comprueba
también el destino inexistente; las respuestas 404 tienen el mismo cuerpo y
los datos de negocio se conservan. Sobre pedidos propios se mantiene el 400.

No se fabrica un RED de implementación inicial: el código ya existía al
comenzar la revisión. La ampliación final de instantáneas de intentos tiene
Green inicial sobre ese comportamiento existente.

## Ejecuciones finales

Desde la raíz del repositorio, con su entorno virtual y PostgreSQL local:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest apps/orders/tests/test_views.py -k 'payment or pending_order_detail' -q -p no:cacheprovider --tb=no
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=no
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python manage.py check --database default
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python manage.py makemigrations --check --dry-run
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python manage.py migrate --check
.venv/bin/ruff check . --no-cache
.venv/bin/ruff format --check . --no-cache
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

| Comprobación | Resultado observado |
|---|---|
| RF-07 | `28 passed, 17 deselected in 8.38s` |
| Batería completa | `200 passed in 28.02s` |
| Django y base de datos | `System check identified no issues (0 silenced).` |
| Migraciones por generar | `No changes detected` |
| Migraciones por aplicar | Sin pendientes; `orders.0004` ya estaba aplicada |
| Ruff | `All checks passed!` |
| Formato Python | `116 files already formatted` |
| Dependencias | `No broken requirements found.` |
| Diff de trabajo y del commit | Sin espacios sobrantes ni errores de parche |

pip indicó que su caché no era escribible y la deshabilitó; la comprobación de
dependencias terminó correctamente. No se modificaron dependencias ni permisos
de caché para ocultar el aviso.

## Límites y reproducibilidad

- Las pruebas usan PostgreSQL y su base de pruebas independiente; no utilizan
  SQLite ni producen pagos en la base de desarrollo.
- La concurrencia comprueba dos PID de backend PostgreSQL distintos y ambos
  casos de claves iguales/diferentes, con un único intento persistido.
- El rollback provoca el fallo después de insertar el intento y antes de guardar
  paid, y compara pedidos, líneas, intentos y carrito tras abortar.
- CSRF real se comprueba con `Client(enforce_csrf_checks=True)` para el acceso
  anónimo; el formulario de pago se comprueba en el HTML del detalle.
- No se acredita revisión visual manual, capturas, despliegue, pasarela real,
  emisión de derechos, rechazo/reintento ni API privada.
- El commit conserva únicamente los cambios propios de RF-07; otros cambios
  locales de requisitos y metodología permanecen sin incluir.

El identificador del commit se obtiene con
`git log -1 -- docs/evidence/RF-07/quality-gate-2026-10-02.md`.
