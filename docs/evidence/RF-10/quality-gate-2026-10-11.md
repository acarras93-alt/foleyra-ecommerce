# RF-10 parcial — Puerta de calidad del 2026-10-11

Ejecutada por Codex sobre el árbol local basado en `6a0a27c`, preservando los
cambios del desarrollador. Python del entorno virtual del repositorio y
PostgreSQL del servicio `db` de Docker Compose, imagen `postgres:18.6-alpine`.

## Resultados observados

| Comando | Resultado |
|---|---|
| `docker compose ps` | `db` saludable, puerto local 5432 |
| `.venv/bin/python manage.py check --database default` | Sin incidencias |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | `No changes detected`, sin advertencias de conexión en la ejecución final |
| `.venv/bin/python manage.py migrate --check` | Código de salida 0; sin migraciones pendientes |
| `.venv/bin/python manage.py showmigrations catalog orders` | Migraciones aplicadas hasta `catalog.0003` y `orders.0008` |
| `.venv/bin/python -m pytest -q apps/orders/tests/test_services.py apps/orders/tests/test_views.py -k 'license or grant or product_reference or unmapped'` | `30 passed, 72 deselected in 3.03s` |
| `.venv/bin/python -m pytest -q` | `250 passed in 35.28s` |
| `.venv/bin/ruff check --no-cache .` | `All checks passed!` |
| `.venv/bin/ruff format --no-cache --check .` | `120 files already formatted` |
| `.venv/bin/pip check` | `No broken requirements found` |
| `git diff --check` | Sin incidencias en los cambios rastreados |
| `git diff --cached --check` | Sin incidencias, incluidos los archivos nuevos preparados |

Revisión documental adicional: 54 enlaces locales de los Markdown preparados,
todos con destino existente. La revisión de los 38 archivos preparados no
detectó `.env`, medios privados ni valores de las credenciales locales en sus
contenidos. No se muestran ni se incorporan secretos a la evidencia.

La recogida previa encontró `250 tests collected`. Esto no se utilizó como
resultado de ejecución: los resultados Green proceden de los comandos pytest
registrados arriba.

## Incidencias resueltas y límites

- Inicialmente Docker estaba detenido y no había conexión a PostgreSQL. El
  desarrollador inició Docker Desktop; todas las comprobaciones finales con
  base de datos se realizaron después de comprobar `db` saludable.
- Ruff detectó un import desordenado en `apps/orders/tests/test_services.py`.
  Se corrigió con `.venv/bin/ruff check --no-cache --fix
  apps/orders/tests/test_services.py` y el control general posterior pasó.
- pip deshabilitó su caché por permisos; la comprobación de dependencias
  terminó correctamente.
- Las migraciones existentes ya estaban aplicadas. No se migró la base de
  desarrollo, no se cambiaron dependencias ni se añadieron reglas de negocio.
- Hay una prueba vacía con `pass`, identificada en la [matriz parcial](README.md).
  La cifra de pytest incluye ese caso; no se presenta como cobertura real.
- RF-10 sigue parcialmente implementado. No se certifican su cierre completo,
  capturas, instalación limpia, audios reales ni despliegue en producción.
