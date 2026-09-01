# Foleyra

Foleyra es un MVP de comercio electrónico de productos sonoros construido con
Python, Django, Django REST Framework y PostgreSQL.

## Estado actual

- El proyecto es un monolito modular de Django con las aplicaciones de negocio agrupadas bajo `apps`.
- PostgreSQL 18.6 es la única base de datos admitida y se ejecuta localmente mediante Docker Compose.
- El modelo de usuario activo es `users.User`, definido antes de la primera migración.
- `apps.core` proporciona una página de inicio pública en `/`, con enrutamiento y renderizado de plantillas verificados.
- `apps.catalog` contiene los modelos de categorías, productos, tipos de licencia y ofertas. La lista pública `/catalog/` muestra productos disponibles, excluye productos inactivos, muestra un estado vacío comprensible, pagina en bloques de 12 con enlaces anterior y siguiente y presenta como `Desde <precio> EUR` el mínimo de las ofertas y tipos de licencia activos. Admite búsqueda por texto normalizado (`q`), filtro combinado por `category` y `license`, ordenación por `name`/`-name`/`price`/`-price`, conserva el estado de consulta al paginar y responde 400 ante parámetros conocidos inválidos.
- El detalle público `/catalog/{slug}/` muestra los metadatos técnicos y las ofertas activas de un producto disponible. Ofrece un reproductor cuando existe una preview y muestra un aviso cuando no está disponible.
- Las previews usan una raíz pública independiente y pueden obtenerse mediante `/media/` en desarrollo con `DEBUG=True`. Los archivos maestros permanecen en almacenamiento privado sin URL pública, y su nombre, ruta y contenido no se incluyen en el HTML ni en el contexto público. La entrega autorizada del maestro corresponde a RF-11 y continúa fuera del alcance implementado.
- RF-01, RF-02, RF-03, RF-12 y RF-15 están `Aprobado`, salvo RF-03 que está `Implementado` (los siete criterios de aceptación están implementados y comprobados localmente; pendiente evidencia formal por criterio y commit para declararlo `Verificado`). RF-01 y RF-02 disponen de implementación y pruebas. Los requisitos de compra y las funciones privadas continúan en estado `Propuesto`.

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
público de la página de inicio. Las pruebas de `apps.catalog` cubren el flujo
público catálogo-detalle con PostgreSQL, la entrega HTTP anónima de la preview
desde almacenamiento temporal y la exclusión del archivo maestro del HTML y
del contexto público.

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
