# Evidencias de la fase 01

## Objetivo

Conservar evidencias reproducibles de la inicialización de Django y de la
primera migración sobre PostgreSQL. Las capturas complementan al historial de
Git y a las pruebas; no los sustituyen.

## Reglas para las capturas

- Mostrar el comando y su salida completa siempre que sea posible.
- No mostrar `.env`, contraseñas, claves, tokens ni datos personales.
- Recortar pestañas, notificaciones o rutas personales que no aporten valor.
- No modificar la salida para ocultar errores: corregirlos y repetir el comando.
- Usar los nombres propuestos para mantener la trazabilidad.
- Revisar cada imagen antes de incorporarla al repositorio.

## Capturas requeridas

### 01 — Versiones aprobadas

Nombre: `01-versiones.png`.

```bash
python --version
python -m django --version
python -c "import rest_framework, psycopg; print(rest_framework.VERSION); print(psycopg.__version__)"
```

Debe mostrar Python 3.12.13, Django 5.2.17, DRF 3.18.0 y Psycopg 3.3.4.

### 02 — Integridad de dependencias

Nombre: `02-pip-check.png`.

```bash
python -m pip check
```

Debe finalizar sin dependencias incompatibles.

### 03 — PostgreSQL saludable

Nombre: `03-postgresql-saludable.png`.

```bash
docker compose ps
docker compose exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();"'
```

Debe mostrar el servicio `db` saludable y PostgreSQL 18.6.

### 04 — Configuración de Django

Nombre: `04-django-check.png`.

```bash
python manage.py check --database default
python manage.py makemigrations --check --dry-run
```

Debe indicar que no existen problemas ni cambios de modelo sin migración.

### 05 — Migraciones aplicadas

Nombre: `05-migraciones.png`.

```bash
python manage.py migrate --check
python manage.py showmigrations users
```

`users.0001_initial` debe aparecer marcada como aplicada. El primer comando no
produce salida cuando no hay migraciones pendientes; su estado correcto puede
capturarse junto con el segundo comando.

### 06 — Usuario personalizado en PostgreSQL

Nombre: `06-usuario-personalizado.png`.

```bash
python manage.py shell -c "from django.conf import settings; from django.contrib.auth import get_user_model; from django.db import connection; User = get_user_model(); tables = connection.introspection.table_names(); print(settings.AUTH_USER_MODEL); print(User._meta.db_table); print(User._meta.db_table in tables); print('auth_user' in tables)"
```

La salida esperada es `users.User`, `users_user`, `True` y `False`.

### 07 — Pruebas y calidad

Nombre: `07-pruebas-calidad.png`.

```bash
pytest -q
ruff check .
ruff format --check .
```

Debe mostrar tres pruebas superadas y las comprobaciones de Ruff correctas.

### 08 — Commits del checkpoint

Nombre: `08-commits.png`.

```bash
git log -4 --oneline
git status --short --branch
```

Debe mostrar los cuatro commits de la fase y un árbol de trabajo limpio.

### 09 — Estructura del proyecto

Nombre: `09-estructura-django.png`.

Capturar el explorador de Visual Studio Code mostrando, como mínimo,
`config`, `apps/users`, `manage.py`, `pytest.ini` y la migración inicial.

## Cierre de las evidencias

Después de añadir y revisar las imágenes:

```bash
git status --short
git diff --check
```

Commit recomendado:

```text
docs: add phase one installation evidence
```
