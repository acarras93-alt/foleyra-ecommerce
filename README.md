# Foleyra

Foleyra es un MVP de comercio electrónico de productos sonoros construido con
Python, Django, Django REST Framework y PostgreSQL.

## Estado actual

- El proyecto es un monolito modular de Django con las aplicaciones de negocio agrupadas bajo `apps`.
- PostgreSQL 18.6 es la única base de datos admitida y se ejecuta localmente mediante Docker Compose.
- El modelo de usuario activo es `users.User`, definido antes de la primera migración.
- `apps.core` proporciona una página de inicio pública en `/`, con enrutamiento y renderizado de plantillas verificados.
- `apps.catalog` contiene el modelo base y su migración inicial para categorías, productos, tipos de licencia y ofertas. La lista pública mínima `/catalog/` muestra productos disponibles, excluye productos inactivos, muestra un estado vacío comprensible, pagina en bloques de 12 con enlaces anterior y siguiente, presenta el precio mínimo de las ofertas activas como `Desde <precio> EUR` y carga categorías y ofertas activas sin N+1. El detalle público `/catalog/{slug}/` muestra los metadatos técnicos y las ofertas activas de un producto disponible; preview, filtros y API continúan pendientes.
- RF-01, RF-02, RF-03, RF-12 y RF-15 están `Aprobado`. El checkpoint del catálogo habilita iniciar el ciclo test-first con CA-RF01-01; los requisitos de compra y las funciones privadas continúan en estado `Propuesto`.

## Requisitos locales

- Python 3.12.13.
- Docker Desktop.
- Un entorno virtual creado con las dependencias bloqueadas del proyecto.
- Un archivo `.env` configurado sin exponer sus valores.

Consulta el [manual de instalación](docs/installation.md) para preparar el
entorno desde cero. Después de configurar las variables de entorno, inicia
PostgreSQL con:

```bash
docker compose up -d db
docker compose ps
```

## Verificación

Con el entorno virtual activo y PostgreSQL disponible, ejecuta:

```bash
set -e
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
`users` valida además que dicho usuario puede persistirse en PostgreSQL. Las
pruebas de `apps.core` verifican la URL raíz, el acceso anónimo y el contenido
público de la página de inicio.

## Documentación

- [Stack tecnológico](docs/technology-stack.md)
- [Requisitos funcionales](docs/requirements/functional-requirements.md)
- [Requisitos no funcionales](docs/requirements/non-functional-requirements.md)
- [Checkpoint de decisiones del catálogo](docs/requirements/catalog-decision-checkpoint.md)
- [Flujo manual, Copilot, pruebas y documentación del catálogo](docs/catalog-development-workflow.md)
- [Decisiones de arquitectura](docs/decisions/)
- [Bitácora técnica](docs/technical-log.md)
- [Evidencias del checkpoint inicial](docs/evidence/phase-01/README.md)
- [Registro de desarrollo asistido por IA](docs/ai-assisted-development.md)
