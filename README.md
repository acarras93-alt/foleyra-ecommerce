# Foleyra

Foleyra es un MVP de comercio electrónico de productos sonoros construido con
Python, Django, Django REST Framework y PostgreSQL.

## Estado actual

- El proyecto es un monolito modular de Django con las aplicaciones de negocio agrupadas bajo `apps`.
- PostgreSQL 18.6 es la única base de datos admitida y se ejecuta localmente mediante Docker Compose.
- El modelo de usuario activo es `users.User`, definido antes de la primera migración.
- Los requisitos funcionales del catálogo y del flujo de compra permanecen en estado `Propuesto`; no están implementados.

## Requisitos locales

- Python 3.12.13.
- Docker Desktop.
- Un entorno virtual creado con las dependencias bloqueadas del proyecto.
- Un archivo `.env` configurado sin exponer sus valores.

Consulta el [manual de instalación](docs/installation.md) para preparar el
entorno desde cero. Después de configurar las variables de entorno, inicia
PostgreSQL con:

```bash
docker compose up -d
```

## Verificación

Con el entorno virtual activo y PostgreSQL disponible, ejecuta:

```bash
.venv/bin/python manage.py check --database default
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py migrate --check
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pip check
```

Las pruebas de entorno comprueban que Django usa PostgreSQL y que resuelve
`users.User` como el modelo de usuario principal. La prueba de la aplicación
`users` valida además que dicho usuario puede persistirse en PostgreSQL.

## Documentación

- [Stack tecnológico](docs/technology-stack.md)
- [Requisitos funcionales](docs/requirements/functional-requirements.md)
- [Decisiones de arquitectura](docs/decisions/)
- [Bitácora técnica](docs/technical-log.md)
- [Evidencias del checkpoint inicial](docs/evidence/phase-01/README.md)
- [Registro de desarrollo asistido por IA](docs/ai-assisted-development.md)
