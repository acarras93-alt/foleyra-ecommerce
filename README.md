# Foleyra

Foleyra es un proyecto de comercio electrónico de productos sonoros, construido
con Python, Django, Django REST Framework y PostgreSQL como proyecto final de
mi formación.

**Estado: MVP implementado; documentación y paquete de entrega en cierre.**
Incluye catálogo web y API pública de lectura, cuentas, carrito, pedidos,
pagos simulados, licencias y descarga protegida del maestro adquirido. El
proyecto usa PostgreSQL y conserva los maestros fuera del almacenamiento
público. El pago es simulado y no realiza cargos reales.

**Alcance de entrega confirmado con el instructor, registrado el 2026-10-21:**
el cierre requiere RF-11, RF-15 y el recorrido web completo, con evidencias y
una instalación reproducible. La API privada (RF-13 y RF-14) y la clasificación
jerárquica del catálogo (RF-16) quedan como evolutivos posteriores a la entrega.

## Recorrido del proyecto

Un visitante puede explorar el catálogo, buscar productos, filtrar por categoría
y licencia y escuchar las previews disponibles. Un usuario registrado puede
preparar un carrito y convertirlo en un pedido con los datos de compra guardados.
Desde «Mis pedidos» puede consultar el listado privado y abrir cada detalle,
conservando los datos históricos aunque cambie el catálogo. Desde el detalle
de un pedido pendiente puede simular un pago aprobado sin consumir su carrito
actual ni efectuar un cobro real.

La aprobación emite un permiso por línea en la misma transacción que el pago.
«Mis licencias» permite consultar los permisos activos de pedidos pagados,
abrir sus condiciones históricas y descargar el maestro capturado por cada línea
del pedido. El enlace requiere iniciar sesión y el servidor vuelve a comprobar
la propiedad, el pago y el derecho antes de enviar el archivo. Las descargas son
individuales; no se genera un ZIP de todos los sonidos.

El trabajo reúne modelado de datos, autenticación, vistas y formularios Django,
una API REST de lectura, operaciones atómicas y pruebas con PostgreSQL.
La separación entre previews públicas y archivos maestros privados es una de
las decisiones principales del diseño.

Para una revisión rápida del portfolio:

- Catálogo web: `/catalog/` y detalle de cada producto.
- API pública: `/api/v1/catalog/products/`.
- Pedidos propios (requieren sesión): `/orders/` y `/orders/{order_id}/`.
- Permisos propios (requieren sesión): `/licenses/` y `/licenses/{license_id}/`.
- Código de negocio: `apps/catalog/`, `apps/cart/` y `apps/orders/`.
- Decisiones y seguimiento: [documentación técnica](#documentación).

Los datos del catálogo y los archivos de audio deben prepararse en el entorno
local. La presencia de una ruta no implica que exista una demo pública desplegada.

## Estado actual

- El proyecto es un monolito modular de Django con las aplicaciones de negocio agrupadas bajo `apps`.
- PostgreSQL 18.6 es la única base de datos admitida y se ejecuta localmente mediante Docker Compose.
- El modelo de usuario activo es `users.User`, definido antes de la primera migración.
- RF-04 está `Verificado`: la web ofrece registro, inicio de sesión mediante
    `username` y cierre de sesión por formulario `POST` con CSRF en
    `/accounts/register/`, `/accounts/login/` y `/accounts/logout/`. La
    autenticación de API continúa fuera de alcance hasta RF-13.
- RF-05 está `Aprobado` e implementado: un cliente autenticado puede consultar
    su carrito privado, añadir ofertas disponibles y eliminar líneas propias con
    `POST` y CSRF. El carrito usa precios actuales, conserva las líneas que dejan
    de estar disponibles fuera del total y no mantiene historial. La equivalencia
    con una API autenticada queda como evolutivo de RF-13.
- RF-06 está `Implementado`: un cliente autenticado puede convertir su carrito
    de ofertas disponibles en un pedido histórico `pending_payment` mediante
    `POST /orders/create/`. La operación captura los datos de compra, calcula el
    total en EUR, vacía el carrito de forma atómica y rechaza carritos vacíos u
    ofertas no disponibles. La API privada queda como evolutivo de RF-14.
- RF-07 está `Verificado`: el propietario puede simular una aprobación mediante
    `POST /orders/{order_id}/payments/simulate/`. Pedido e intento se guardan en
    una transacción; el replay no duplica pagos y un pedido pagado con otra clave
    responde 409. La propiedad se comprueba antes de rechazar campos extra.
    El carrito y las líneas históricas se conservan. Las [evidencias de RF-07](docs/evidence/RF-07/README.md)
    registran 28 casos del requisito y 200 pruebas totales con PostgreSQL.
- RF-08 está `Verificado`: el mismo POST admite `result=failed`, conserva el
    pedido pendiente y registra el rechazo. Reintentar con una clave nueva puede
    aprobar el pago conservando los intentos anteriores. El detalle muestra el
    historial propio ordenado con resultado y fecha; su consulta no modifica datos.
    Las pruebas cubren seguridad, idempotencia, concurrencia y rollback.
    El formulario del pedido pendiente permite elegir aprobación o rechazo
    simulado. Tras un rechazo se puede reintentar con una clave nueva. Véanse las
    [evidencias de RF-08](docs/evidence/RF-08/README.md).
- RF-09 está `Implementado`: `/orders/` muestra únicamente los pedidos propios,
    ordenados por fecha de creación e ID descendentes, con fecha y enlace al
    detalle. `/orders/{order_id}/` presenta el pedido y sus líneas históricas;
    los pedidos ajenos e inexistentes responden con el mismo 404 genérico.
    La navegación autenticada incluye «Mis pedidos». Las consultas no alteran
    pedidos ni carritos y la prueba del detalle verifica un número constante y
    acotado de consultas con una y diez líneas. La cobertura de entidades futuras
    y las capturas visuales se detallan en las [evidencias de RF-09](docs/evidence/RF-09/README.md).
- RF-10 está `Verificado`: `LicenseGrant` registra un permiso por línea al
    aprobar el pago, con unicidad, replay y rollback transaccional. Listado y
    detalle privados muestran condiciones históricas, con login, 404 uniforme,
    rechazo de escrituras y consultas constantes. El checkout captura las
    referencias estables de producto y tipo de licencia y las condiciones
    completas. Carrito, checkout y pago rechazan recompras y posibles coincidencias
    con derechos antiguos sin identificar; la aprobación también rechaza líneas
    propias sin referencias. Las condiciones incompletas impiden checkout/pago.
    Dos servicios explícitos regularizan permisos faltantes y documentación
    histórica revisada. La matriz CA01–CA16 y los límites están en
    [RF-10](docs/evidence/RF-10/README.md).
- RF-11 implementa la preparación del maestro, su captura en cada línea del
    pedido y la descarga autorizada desde «Mis licencias». La preparación valida
    WAV/BWF, FLAC y AIFF con un mínimo de 48 kHz y 24 bits; reemplazar el maestro
    del catálogo conserva el que quedó asociado a compras anteriores. Checkout
    y pago rechazan maestros no preparados o desaparecidos sin cambios
    parciales. El enlace entrega los bytes del maestro histórico como adjunto;
    no ofrece una descarga masiva ni genera un ZIP.
- `apps.core` proporciona una página de inicio pública en `/`, con la marca
    Foleyra, la presentación «Biblioteca de sonidos para proyectos audiovisuales»,
    acceso al catálogo y una indicación del carácter académico y simulado de las compras.
- El recorrido web incluye navegación compartida según autenticación,
    previews y selección de ofertas desde el catálogo, retorno al catálogo desde
    el carrito y navegación entre licencias y sus pedidos. Son avances parciales
    de RF-17; no acreditan el cierre del recorrido completo. RF-16, clasificación
    por familias y subfamilias, continúa propuesto y sin implementar, como
    evolutivo posterior a la entrega.
- `apps.catalog` contiene los modelos de categorías, productos, tipos de licencia y ofertas. La lista pública `/catalog/` muestra productos disponibles, excluye productos inactivos, muestra un estado vacío comprensible, pagina en bloques de 12 con enlaces anterior y siguiente y presenta como `Desde <precio> EUR` el mínimo de las ofertas y tipos de licencia activos. Admite búsqueda por texto normalizado (`q`), filtro combinado por `category` y `license`, ordenación por `name`/`-name`/`price`/`-price`, conserva el estado de consulta al paginar y responde 400 ante parámetros conocidos inválidos.
- El detalle público `/catalog/{slug}/` muestra los metadatos técnicos y las ofertas activas de un producto disponible. Ofrece un reproductor cuando existe una preview y muestra un aviso cuando no está disponible.
- La API pública de solo lectura `/api/v1/catalog/products/` y `/api/v1/catalog/products/{slug}/` ofrece la misma selección disponible en web, filtros y ordenación aprobados, paginación de 12 elementos, detalle con previews y ofertas públicas, y errores JSON contractuales. No expone archivos maestros ni campos administrativos.
- Las previews usan una raíz pública independiente y pueden obtenerse mediante
    `/media/` en desarrollo con `DEBUG=True`. Los maestros se guardan en
    `private_media/`, sin URL pública; solo se entregan desde la ruta protegida
    de una licencia propia y pagada.
- RF-15 está verificado en el alcance aprobado CA-RF15-01 a CA-RF15-07: el Admin
    permite gestionar el catálogo y consultar pedidos, pagos y licencias en modo
    de solo lectura. La puerta de calidad del 2026-10-26 registra 434 pruebas
    aprobadas y los controles de Django, migraciones, Ruff y dependencias
    superados. Los criterios adicionales CA-RF15-08 a CA-RF15-12 permanecen
    propuestos y fuera del alcance de esta entrega.

## Cierre y alcance de entrega

El recorrido manual descrito en el [manual de instalación](docs/installation.md)
cubre catálogo, carrito, pedido, pago simulado, licencia y descarga. Sus
capturas complementan las pruebas automatizadas; no las sustituyen. La puerta
de calidad registrada para el 2026-10-26 obtuvo 434 pruebas aprobadas. Consulta
las [evidencias de RF-15](docs/evidence/RF-15/quality-gate-2026-10-26.md) y los
[requisitos funcionales](docs/requirements/functional-requirements.md).

La entrega acordada contiene el código fuente y un documento final PDF o DOC
con objetivos, tecnología, base de datos, requisitos, instalación, capturas,
conclusiones y evolutivos. Los datos de catálogo y archivos de audio se preparan
localmente; el repositorio no incluye la biblioteca comercial ni los maestros
privados. No incluyas `.env`, `.venv`, bases locales ni secretos en el ZIP.

## Evolutivos posteriores a la entrega

- **RF-13 y RF-14 · API privada:** gestionar carrito, checkout, pagos simulados,
  pedidos y licencias desde otros clientes, reutilizando las reglas de la web.
- **RF-16 · Clasificación jerárquica:** ampliar el catálogo mediante familias
  y subfamilias sonoras y sus consultas asociadas.

Estos requisitos conservan su estado `Propuesto` y sus contratos como referencia
para futuras versiones. No bloquean la entrega acordada con el instructor y
deben identificarse como evolutivos en las conclusiones y la memoria.

## Requisitos locales

- Python 3.12.13.
- Docker Desktop.
- Un entorno virtual creado con las dependencias bloqueadas del proyecto.
- Un archivo `.env` configurado sin exponer sus valores.

El [manual de instalación](docs/installation.md) explica cómo crear el entorno,
preparar PostgreSQL, configurar el catálogo de demostración y recorrer la
compra y descarga desde la web. Desde la raíz del repositorio, en macOS o Linux,
prepara un entorno nuevo:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
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

Abre `http://127.0.0.1:8000/`. El Admin permite gestionar categorías,
productos, tipos de licencia y ofertas, y consultar pedidos, pagos y licencias
históricos en modo de solo lectura. La preparación del maestro se realiza con
el servicio documentado en el manual; el Admin no tiene un formulario de carga
de maestros. Estos pasos describen una instalación local de desarrollo, no un
despliegue en producción.

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
del contexto público. Las pruebas de `apps.orders` cubren la conversión del
carrito en pedido histórico, la persistencia de `created_at` y los selectores de
consulta propia con orden estable, aislamiento por propietario y carga de líneas.
Las pruebas web verifican listado vacío, campos históricos, navegación, 404
uniforme, conservación del histórico tras cambios del catálogo, ausencia de
efectos laterales sobre pedidos y carrito y consultas acotadas del detalle.
RF-07 añade pruebas de aprobación, validación, idempotencia, concurrencia entre
conexiones PostgreSQL independientes y rollback sin efectos parciales.
El incremento de RF-10 amplía esta cobertura con emisión y replay de permisos,
rollback durante la emisión, aislamiento, condiciones históricas, navegación,
ausencia de escrituras en consultas, detección de N+1, referencias estables,
recompra, regularización y validación de condiciones. Los resultados y límites
están en [la evidencia de cierre de RF-10](docs/evidence/RF-10/README.md).

## Documentación

- [Stack tecnológico](docs/technology-stack.md)
- [Requisitos funcionales](docs/requirements/functional-requirements.md)
- [Requisitos no funcionales](docs/requirements/non-functional-requirements.md)
- [Plan de cierre del MVP y metodología por criterio](docs/requirements/mvp-implementation-plan.md)
- [Checkpoint de decisiones del catálogo](docs/requirements/catalog-decision-checkpoint.md)
- [Flujo manual, Copilot, pruebas y documentación del catálogo](docs/catalog-development-workflow.md)
- [Decisiones de arquitectura](docs/decisions/)
- [Bitácora técnica](docs/technical-log.md)
- [Evidencias del checkpoint inicial](docs/evidence/phase-01/README.md)
- [Registro de desarrollo asistido por IA](docs/ai-assisted-development.md)
