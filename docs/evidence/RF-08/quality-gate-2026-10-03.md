# Verificación automatizada de RF-08 — 2026-10-03

## Comprobaciones ejecutadas

Desde la raíz del repositorio, con el entorno virtual existente y PostgreSQL:

| Comando | Resultado observado |
|---|---|
| `.venv/bin/python -m pytest apps/orders/tests -q` | `75 passed in 22.67s`, antes de ampliar la comprobación del historial. |
| `.venv/bin/python -m pytest apps/orders/tests/test_views.py::test_order_detail_shows_only_own_payment_history_without_changes -q` | `1 passed in 1.12s`, tras completar fecha, desempate, resultados visibles y capturas de ambos clientes. |
| `.venv/bin/python -m pytest -q` | `219 passed in 32.39s`, batería final con la ampliación incluida. |
| `.venv/bin/python manage.py check --database default` | `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | `No changes detected`. |
| `.venv/bin/python manage.py migrate --check` | Correcto, sin migraciones pendientes de aplicar. |
| `.venv/bin/python manage.py showmigrations orders` | `0001` a `0005` aplicadas; incluida `0005_alter_paymentattempt_result`. |
| `.venv/bin/ruff check . --no-cache` | `All checks passed!` |
| `.venv/bin/ruff format --check . --no-cache` | `118 files already formatted`. |
| `.venv/bin/python -m pip check` | `No broken requirements found.` |
| `git diff --check` y `git diff --cached --check` | Correctos, sin errores de espacios ni de parche. |

pip deshabilitó su caché por falta de permiso de escritura; la comprobación de
dependencias terminó correctamente. No se cambian dependencias ni permisos de
caché para ocultar ese aviso. Esta revisión no genera ni aplica migraciones:
comprueba la migración generada y aplicada previamente por el desarrollador.

Las pruebas finales incluyen la regresión de pedidos, los cinco escenarios de
seguridad del reintento, concurrencia y rollback. La ampliación del historial
parte de comportamiento existente y obtiene Green inicial; no se fabrica Red.

## Alcance de las garantías

La prueba del historial usa tres intentos propios: dos comparten fecha exacta y
el de mayor ID queda primero; un tercero tiene un ID aún mayor pero fecha
anterior y debe quedar al final. Comprueba el texto de resultado y fecha dentro
de cada fila y conserva los registros de ambos propietarios.

Las pruebas de eficiencia usan las relaciones renderizadas, con uno/diez
intentos y una/diez líneas. Exigen el mismo número de consultas y un máximo de
cinco en la configuración actual. No son una medición de latencia o carga.

Las pruebas concurrentes usan `transaction=True`, dos clientes, dos conexiones
PostgreSQL y límites de espera. La prueba mixta comprueba ambos resultados
permitidos por el contrato, sin asumir qué petición gana; una ejecución no
certifica todos los posibles entrelazados. La regresión de RF-07 verifica que
un error técnico posterior a insertar el intento revierte la escritura.

## Reproducibilidad del cierre

El código que se versiona conserva las pruebas de RF-07 y añade RF-08. La
revisión no modifica producción, además de incorporar al commit el desarrollo
ya realizado. La selección documental incluye RF-08 y las referencias de RF-07
que ahora deben describir el rechazo como implementado. Los cambios locales de
otros requisitos y metodología no forman parte de este commit.

No se certifican capturas de navegador, uso manual, pasarela real, derechos,
descargas ni API privada. Véase la [matriz y límites](README.md).
