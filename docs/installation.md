# Manual de instalación

Este documento describe cómo preparar y ejecutar el proyecto desde un entorno limpio.

## 1. Prerrequisitos

- Git.
- Python 3.12.13.
- pyenv.
- Docker Desktop.
- Visual Studio Code.

## 2. Creación del entorno virtual

[Comandos reales utilizados]

## 3. Instalación de dependencias bloqueadas

[Comandos pip-tools y pip-sync]

## 4. Configuración de variables de entorno

[Creación de .env desde .env.example, sin mostrar secretos]

## 5. Arranque de PostgreSQL

[Comandos Docker Compose]

## 6. Verificaciones

[Versiones, pip check, pg_isready y consulta SELECT version()]

## 7. Django

### 7.1. Estructura inicial

El proyecto utiliza `config` para la configuración global y agrupa las
aplicaciones de negocio bajo `apps`. La primera aplicación es `apps.users`,
que define el modelo de usuario personalizado `users.User`.

La variable `AUTH_USER_MODEL` se configuró antes de generar o aplicar ninguna
migración. La conexión `default` utiliza exclusivamente el backend de
PostgreSQL y obtiene sus credenciales desde `.env`.

### 7.2. Generación y aplicación de las migraciones iniciales

Con el contenedor de PostgreSQL en estado saludable:

```bash
python manage.py makemigrations users
python manage.py migrate --plan
python manage.py migrate
```

La primera ejecución creó las tablas estándar de Django y la tabla
`users_user`. No se creó la tabla `auth_user` del modelo sustituido.

La migración `catalog.0001_initial` se generó con Django, se revisó mediante
`migrate catalog --plan` y se aplicó después sobre PostgreSQL. Crea las tablas
de categorías, productos, tipos de licencia y ofertas producto-licencia; no
incorpora modelos de suscripción, pedido, pago ni descarga.

### 7.3. Verificaciones

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
ruff check .
ruff format --check .
```

Estas comprobaciones validan la configuración de Django, la ausencia de
cambios de modelo sin migración, el uso del usuario personalizado, su
persistencia en PostgreSQL y la calidad estática del código.

### 7.4. Evidencias del checkpoint

El inventario de capturas, sus comandos reproducibles y las reglas para no
exponer secretos se encuentran en
[`docs/evidence/phase-01/README.md`](evidence/phase-01/README.md).

El prompt empleado durante esta inicialización y el alcance real de la
asistencia de IA se registran en
[`docs/ai-assisted-development.md`](ai-assisted-development.md).
