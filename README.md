# Foleyra

Foleyra es un proyecto de comercio electrónico de productos sonoros, construido
con Python, Django, Django REST Framework y PostgreSQL como proyecto final de
mi formación.

**Estado: MVP en desarrollo.** Ya incluye catálogo web y API pública, cuentas de
usuario, carrito privado y creación de pedidos pendientes de pago. El flujo
completo de compra y entrega de archivos todavía no está terminado.

## Recorrido del proyecto

Un visitante puede explorar el catálogo, buscar productos, filtrar por categoría
y licencia y escuchar las previews disponibles. Un usuario registrado puede
preparar un carrito y convertirlo en un pedido con los datos de compra guardados.

El trabajo reúne modelado de datos, autenticación, vistas y formularios Django,
una API REST de lectura, operaciones atómicas y pruebas con PostgreSQL.
La separación entre previews públicas y archivos maestros privados es una de
las decisiones principales del diseño.

Para una revisión rápida del portfolio:

- Catálogo web: `/catalog/` y detalle de cada producto.
- API pública: `/api/v1/catalog/products/`.
- Código de negocio: `apps/catalog/`, `apps/cart/` y `apps/orders/`.
- Decisiones y seguimiento: [documentación técnica](#documentación).

Los datos del catálogo y los archivos de audio deben prepararse en el entorno
local. La presencia de una ruta no implica que exista una demo pública desplegada.

## Estado actual

- El proyecto es un monolito modular de Django con las aplicaciones de negocio agrupadas bajo `apps`.
- PostgreSQL 18.6 es la única base de datos admitida y se ejecuta localmente mediante Docker Compose.
- El modelo de usuario activo es `users.User`, definido antes de la primera migración.
- RF-04 está `Implementado`: la web ofrece registro, inicio de sesión mediante
	`username` y cierre de sesión por formulario `POST` con CSRF en
	`/accounts/register/`, `/accounts/login/` y `/accounts/logout/`. La
	autenticación de API continúa fuera de alcance hasta RF-13.
- RF-05 está `Aprobado` e implementado: un cliente autenticado puede consultar
	su carrito privado, añadir ofertas disponibles y eliminar líneas propias con
	`POST` y CSRF. El carrito usa precios actuales, conserva las líneas que dejan
	de estar disponibles fuera del total y no mantiene historial. La equivalencia
	con una API autenticada queda pendiente de RF-13.
- RF-06 está `Implementado`: un cliente autenticado puede convertir su carrito
	de ofertas disponibles en un pedido histórico `pending_payment` mediante
	`POST /orders/create/`. La operación captura los datos de compra, calcula el
	total en EUR, vacía el carrito de forma atómica y rechaza carritos vacíos u
	ofertas no disponibles. La consulta de pedidos y la API privada permanecen
	pendientes de RF-09 y RF-14.
- `apps.core` proporciona una página de inicio pública en `/`, con enrutamiento y renderizado de plantillas verificados.
- `apps.catalog` contiene los modelos de categorías, productos, tipos de licencia y ofertas. La lista pública `/catalog/` muestra productos disponibles, excluye productos inactivos, muestra un estado vacío comprensible, pagina en bloques de 12 con enlaces anterior y siguiente y presenta como `Desde <precio> EUR` el mínimo de las ofertas y tipos de licencia activos. Admite búsqueda por texto normalizado (`q`), filtro combinado por `category` y `license`, ordenación por `name`/`-name`/`price`/`-price`, conserva el estado de consulta al paginar y responde 400 ante parámetros conocidos inválidos.
- El detalle público `/catalog/{slug}/` muestra los metadatos técnicos y las ofertas activas de un producto disponible. Ofrece un reproductor cuando existe una preview y muestra un aviso cuando no está disponible.
- La API pública de solo lectura `/api/v1/catalog/products/` y `/api/v1/catalog/products/{slug}/` ofrece la misma selección disponible en web, filtros y ordenación aprobados, paginación de 12 elementos, detalle con previews y ofertas públicas, y errores JSON contractuales. No expone archivos maestros ni campos administrativos.
- Las previews usan una raíz pública independiente y pueden obtenerse mediante `/media/` en desarrollo con `DEBUG=True`. Los archivos maestros permanecen en almacenamiento privado sin URL pública, y su nombre, ruta y contenido no se incluyen en el HTML ni en el contexto público. La entrega autorizada del maestro corresponde a RF-11 y continúa fuera del alcance implementado.
- RF-01, RF-02 y RF-15 están `Aprobado`; RF-03 y RF-12 están `Verificado`.
	Sus evidencias de pruebas y puertas de calidad están disponibles en
	`docs/evidence/RF-03/` y `docs/evidence/RF-12/`. RF-06 permanece
	`Implementado`, no `Verificado`, hasta incorporar sus evidencias. Los
	requisitos privados posteriores continúan en estado `Propuesto`.

## Pendiente para completar el MVP

El catálogo y la API pública de lectura están implementados. Continúan
pendientes la consulta privada de pedidos, los pagos simulados, la entrega autorizada
de archivos maestros y la API privada, de acuerdo con los
[requisitos funcionales](docs/requirements/functional-requirements.md).
Los estados de implementación y verificación se registran por separado.

## Requisitos locales

- Python 3.12.13.
- Docker Desktop.
- Un entorno virtual creado con las dependencias bloqueadas del proyecto.
- Un archivo `.env` configurado sin exponer sus valores.

Desde la raíz del repositorio, en macOS o Linux, prepara un entorno nuevo:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --require-hashes -r requirements-dev.txt
```

Crea un archivo `.env` local a partir de `.env.example` si todavía no tienes
uno. Sustituye los valores de ejemplo de `DJANGO_SECRET_KEY` y
`POSTGRES_PASSWORD` por valores propios y conserva ese archivo fuera de Git.
La configuración de Django y Docker Compose debe usar las mismas credenciales.

Después, inicia PostgreSQL y espera a que `docker compose ps` muestre el
servicio `db` saludable antes de ejecutar las migraciones:

```bash
docker compose up -d db
docker compose ps
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. La cuenta administrativa permite gestionar el
catálogo desde `/admin/`. El [manual de instalación](docs/installation.md)
contiene contexto adicional; algunas secciones siguen pendientes de completar.
Estos pasos describen la configuración existente y no certifican un despliegue
en producción.

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
