# Bitácora técnica

<!-- markdownlint-disable MD024 -->

## 2026-08-17 — Corrección y fijación del entorno Python

### Contexto

El entorno virtual inicial se había creado con Python 3.14.0,
mientras que la versión aprobada para el proyecto era Python 3.12.

### Decisión

Se seleccionó Python 3.12.13 y se fijó mediante `pyenv` y el fichero
`.python-version`.

### Acciones realizadas

1. Se actualizó `pyenv`.
2. Se instaló Python 3.12.13.
3. Se fijó la versión local del proyecto.
4. Se recreó `.venv` con el intérprete correcto.
5. Se generaron los bloqueos de dependencias con `pip-compile`.
6. Se sincronizó el entorno mediante `pip-sync`.
7. Se verificaron las versiones y la integridad de las dependencias.

### Resultado

- Python 3.12.13
- Django 5.2.17
- Django REST Framework 3.18.0
- Psycopg 3.3.4
- pytest 9.1.1
- Ruff 0.16.3
- `pip check`: sin dependencias incompatibles

### Evidencias

Las capturas de instalación y verificación se incorporaron al manual
de instalación

## 2026-08-18 — Cierre del checkpoint de infraestructura

### Completado

- Entorno virtual con Python 3.12.13.
- Dependencias bloqueadas y verificadas.
- Variables de entorno separadas del código.
- PostgreSQL 18.6 ejecutado mediante Docker Compose.
- Conexión con PostgreSQL verificada.
- Decisiones de infraestructura documentadas.
- Commits de infraestructura y documentación realizados.

### Siguiente fase

Crear la estructura Django, configurar PostgreSQL, definir el usuario personalizado y ejecutar la primera migración.

## 2026-08-18 — Inicialización de Django y primera migración

### Contexto

El repositorio tenía el entorno y PostgreSQL preparados, pero todavía no
contenía un proyecto Django. La decisión ADR-003 exige definir el usuario
personalizado antes de la primera migración.

### Decisión

Se creó manualmente el proyecto `config` y la aplicación `apps.users`. El
modelo `users.User` hereda de `AbstractUser`, sin añadir todavía campos que no
estén respaldados por requisitos aprobados.

La conexión `default` usa el backend de PostgreSQL y carga sus parámetros
desde `.env`. Se configuró `AUTH_USER_MODEL = "users.User"` antes de generar la
migración inicial.

### Acciones realizadas

1. Se creó la estructura mínima de Django, incluidas las interfaces WSGI y ASGI.
2. Se registraron Django REST Framework y la aplicación `users`.
3. Se definió y registró el usuario personalizado en Django Admin.
4. Se generó `users.0001_initial`.
5. Se revisó el plan y se aplicaron las migraciones sobre PostgreSQL.
6. Se añadieron pruebas de configuración y persistencia del usuario.
7. Se ejecutaron las comprobaciones de Django, pytest y Ruff.

### Resultado

- Backend de base de datos: PostgreSQL.
- Modelo de usuario activo: `users.User`.
- Tabla de usuario creada: `users_user`.
- Tabla sustituida `auth_user`: no creada.
- Migraciones pendientes: ninguna.
- Funcionalidades del catálogo: no iniciadas.

### Commits del checkpoint

- `feat: initialize Django with custom user`
- `feat: add initial custom user migration`
- `test: verify custom user persistence`
- `docs: record Django initialization checkpoint`

### Siguiente fase

Definir el alcance y los criterios de aceptación del primer incremento del
catálogo antes de iniciar su implementación mediante pruebas.

## 2026-08-18 — Política de desarrollo asistido por IA

### Contexto

La estructura inicial de Django fue creada con asistencia de ChatGPT Codex. Al
cerrar el checkpoint se decidió detener la escritura de código, conservar el
prompt y las evidencias, y utilizar GitHub Copilot como asistente principal en
las fases posteriores.

### Decisión

Registrar de forma explícita la herramienta, el prompt, el alcance, las
verificaciones y los commits. Ninguna sugerencia futura se aceptará sin revisar
el diff, comprender el cambio y ejecutar las pruebas correspondientes.

El desarrollo del catálogo no comenzará hasta que exista un requisito aprobado
con criterios de aceptación suficientes.

### Resultado

- La fase 01 queda cerrada como checkpoint reproducible.
- Existe un inventario de capturas que evita exponer secretos.
- El uso de IA queda documentado con transparencia.
- Existe una guía personal para reproducir y defender las decisiones técnicas.
- El siguiente paso inmediato es de revisión y aprendizaje, no de código.

## 2026-08-18 — Comprobación de arquitectura del entorno Django

### Objetivo

Completar el punto pendiente del manual que exige una prueba de arquitectura
independiente para PostgreSQL y el usuario personalizado.

### Cambios

- Se creó `tests/test_environment.py`.
- Se adaptó la referencia del manual `accounts.User` al modelo real
  `users.User`.
- Se trasladaron a esta prueba las comprobaciones globales que estaban dentro
  de las pruebas específicas de la aplicación `users`.
- La prueba de persistencia del usuario se mantuvo en `apps.users`.

### Comprobaciones ejecutadas

- Prueba de entorno: 2 pruebas superadas.
- Suite completa: 3 pruebas superadas.
- `manage.py check --database default`: sin problemas.
- `makemigrations --check --dry-run`: sin cambios detectados.
- `migrate --check`: sin migraciones pendientes.
- Ruff: análisis y formato correctos.
- `pip check`: sin dependencias incompatibles.

### Resultado y alcance excluido

El proyecto verifica de forma explícita que usa PostgreSQL y que Django resuelve
`users.User` como usuario principal. No se modificaron modelos, migraciones,
dependencias ni funcionalidades del catálogo.

## 2026-08-19 — Documentación del checkpoint de entorno

### Objetivo y alcance

Actualizar el punto de entrada documental del repositorio para describir el
estado verificado del entorno Django. Este cambio no corresponde a un requisito
funcional: los requisitos de catálogo, compra y API continúan en estado
`Propuesto`.

### Decisión y archivos afectados

- GitHub Copilot actualizó `README.md` como resumen del proyecto, sus requisitos
  locales, las comprobaciones disponibles y los enlaces a la documentación
  canónica.
- El README no duplica valores de `.env` ni declara implementadas
  funcionalidades que todavía no están aprobadas.
- Esta entrada registra el cambio en `docs/technical-log.md` sin modificar
  modelos, migraciones, dependencias ni configuración.

### Verificación documental

- `.venv/bin/python -m pytest tests/test_environment.py -q`: 2 pruebas
  superadas.
- `.venv/bin/python -m pytest -q`: 3 pruebas superadas.

### Resultado, riesgos y alcance excluido

El repositorio dispone de un README alineado con ADR-001, ADR-002 y ADR-003,
incluidas las garantías comprobadas de PostgreSQL y `users.User`. El manual de
instalación conserva secciones pendientes de completar y no formó parte de este
cambio. No se implementaron funcionalidades de dominio ni se creó ningún
commit.

## 2026-08-19 — Página de inicio técnica y corrección de su integración

### Objetivo y alcance

Incorporar y verificar la página de inicio pública de `apps.core` como soporte
técnico del proyecto. Este cambio no implementa el catálogo ni ningún otro
requisito funcional: RF-01 y los requisitos posteriores permanecen en estado
`Propuesto`.

### Decisiones y archivos afectados

- GitHub Copilot añadió pruebas HTTP en `apps/core/test_views.py` para verificar
  la URL nombrada `core:home`, el acceso anónimo y el encabezado público.
- Se corrigió el enrutamiento global para importar `include` e integrar
  `apps.core.urls` en la raíz.
- La configuración existente de `apps.core` se completó con el directorio global
  `templates/`, y la vista de inicio pasó a resolver la plantilla existente
  `home.html`.
- Se eliminaron los stubs vacíos de `admin.py`, `models.py` y `tests.py` en
  `apps.core`; las pruebas de la aplicación quedan en `test_views.py`.
- No se modificaron modelos, migraciones, dependencias, otras aplicaciones ni
  requisitos funcionales.

### Comprobaciones ejecutadas

- Estado Red: `.venv/bin/python -m pytest apps/core/test_views.py -q` falló con
  `NameError` al cargar `include` desde la configuración de URLs.
- Estado Green: `.venv/bin/python -m pytest apps/core/test_views.py -q`: 3
  pruebas superadas.
- `.venv/bin/python manage.py check --database default`: sin incidencias.
- `.venv/bin/python manage.py makemigrations --check --dry-run`: sin cambios
  detectados.
- `.venv/bin/python manage.py migrate --check`: sin migraciones pendientes.
- `.venv/bin/python -m pytest -q`: 6 pruebas superadas.
- Ruff, comprobación de formato, `pip check` y `git diff --check`: correctos.

### Resultado, riesgos y alcance excluido

La raíz `/` resuelve la página de inicio pública mediante el namespace
`core:home`, sin acceso a PostgreSQL. La limpieza conserva una única convención
activa de pruebas en la aplicación. El aviso de permisos de la caché de `pip`
no afectó al resultado de `pip check`. No se creó ningún commit.

## 2026-08-20 — Definición documental del catálogo v0.2.0

### Objetivo y alcance

Completar RF-01, RF-02, RF-03, RF-12 y RF-15 hasta el nivel necesario para
revisar sus decisiones antes de aprobar e implementar `apps.catalog`. Organizar
por separado el trabajo manual, la asistencia de GitHub Copilot, las pruebas y
la actualización documental.

### Decisiones propuestas

- El producto describe el contenido y las características técnicas del audio.
- El tipo de licencia describe un destino de uso.
- La oferta producto-licencia contiene precio, moneda y estado; el catálogo
  muestra el precio mínimo activo como `Desde` cuando corresponde.
- Un producto digital no tiene stock físico.
- La preview pública y el archivo maestro privado son archivos y ubicaciones de
  almacenamiento independientes.
- Web y API reutilizarán una consulta de productos disponibles con relaciones
  optimizadas.
- Se ha identificado como decisión bloqueante si el subconjunto de Django Admin
  para el catálogo se adelanta a v0.2.0 o si se usa una fixture temporal.

Estas decisiones continúan en estado propuesto. No se cambió ningún requisito a
`Aprobado` y no se creó código, app, modelo, migración, prueba ni evidencia.

### Archivos documentales

- Se completaron las especificaciones y trazabilidad prevista de RF-01, RF-02,
  RF-03, RF-12 y RF-15.
- Se creó `docs/requirements/catalog-decision-checkpoint.md` con el modelo
  recomendado, decisiones pendientes, criterio de aprobación y puntos para la
  defensa.
- Se creó `docs/catalog-development-workflow.md` con los paquetes de trabajo,
  separación manual/Copilot, ciclo Red-Green, verificaciones y calendario hasta
  el 1 de septiembre.
- README y la guía de Copilot enlazan los nuevos documentos.
- Se registraron divergencias del notebook didáctico antiguo sin modificarlo.

### Comprobaciones ejecutadas

- Primer intento: `manage.py check` y `makemigrations --check --dry-run`
  finalizaron, pero el sandbox bloqueó la conexión local usada por
  `migrate --check`; no se interpretó como un fallo de PostgreSQL.
- Repetición con permiso de red local: `manage.py check --database default`,
  `makemigrations --check --dry-run` y `migrate --check`, correctos y sin
  migraciones pendientes.
- `.venv/bin/python -m pytest -q`: 6 pruebas superadas.
- `.venv/bin/ruff check .`: correcto.
- `.venv/bin/ruff format --check .`: 46 archivos ya formateados.
- `.venv/bin/pip check`: sin dependencias incompatibles; se mostró únicamente
  el aviso conocido de caché sin permisos.
- `git diff --check`: sin errores.

### Resultado y siguiente puerta

La documentación distingue producto, licencia y oferta y evita trasladar el
modelo de suscripción del referente a Foleyra. El siguiente paso no es crear la
app: primero deben resolverse los puntos bloqueantes del checkpoint y cambiar a
`Aprobado` los requisitos que vayan a implementarse. No se creó ningún commit.

## 2026-08-20 — Revisión de RNF y planning de consolidación

### Objetivo y alcance

Convertir los requisitos no funcionales iniciales en contratos medibles para el
catálogo y actualizar el planning de entrega. La fecha del 1 de septiembre pasa
a ser la candidata y congelación funcional; la entrega v1.0.0 se planifica para
el 15 de septiembre si la puerta de calidad está completamente verde.

### Cambios documentales

- Se conservaron y ampliaron RNF-01 a RNF-05.
- Se añadieron RNF-06 a RNF-10 para privacidad del audio, consultas N+1,
  integridad PostgreSQL, contrato determinista y mínimo privilegio.
- Se añadieron RNF-11 a RNF-13 para la puerta de calidad, el calendario de
  consolidación y el control humano del desarrollo asistido por IA.
- RNF-08 y RNF-09 permanecen `Propuesto` porque dependen de aprobar el modelo de
  catálogo y el contrato de consulta. Los demás RNF incorporados se consideran
  restricciones de calidad aprobadas.
- RF-01, RF-02, RF-03, RF-12 y RF-15 enlazan los RNF aplicables.
- El checkpoint exige aceptar RNF-06 a RNF-11 antes de aprobar el catálogo.
- El calendario de `docs/catalog-development-workflow.md` se amplió hasta el 15
  de septiembre y separa implementación, congelación, consolidación y entrega.

### Verificación y alcance excluido

- Se comprobó la estructura de identificadores y dependencias documentales.
- `git diff --check`: sin errores.
- No se modificaron código, configuración, modelos, migraciones, dependencias,
  pruebas automáticas ni evidencias.
- No se ejecutó la suite porque el cambio es exclusivamente documental y no
  altera comportamiento ejecutable.
- No se creó ningún commit.

## 2026-08-21 — Aprobación documental de requisitos del catálogo

### Decisión y alcance

Por confirmación explícita del responsable del proyecto, se cambió el estado de
RF-01, RF-02, RF-03, RF-12 y RF-15 de `Propuesto` a `Aprobado` en
`docs/requirements/functional-requirements.md`.

Esta actualización habilita la planificación e implementación por incrementos
de esos requisitos, pero no resuelve por sí sola las decisiones que el
checkpoint del catálogo mantiene pendientes.

### Comprobaciones y alcance excluido

- Se verificó la coherencia entre los estados del índice y los metadatos de los
  cinco requisitos.
- `git diff --check -- docs/requirements/functional-requirements.md`: sin
  errores.
- No se modificaron código, modelos, migraciones, dependencias, pruebas ni
  evidencias.
- No se creó ningún commit.

## 2026-08-21 — Decisión D-CAT-01: venta unitaria sin suscripción

### Decisión y alcance

El responsable del proyecto aprobó D-CAT-01: cada compra adquiere una licencia
concreta para un producto. Los planes mensuales, las descargas ilimitadas y el
stock físico quedan fuera del MVP y se podrán valorar en una evolución futura.

El modelo actual representa una opción vendible mediante
`ProductLicenseOffer`, que relaciona un producto con un tipo de licencia y un
precio. Se ajustó su prueba para comprobar explícitamente esas asociaciones.
La persistencia de una compra histórica queda fuera de este incremento y
pertenece a RF-06.

### Comprobaciones y bloqueo

- `.venv/bin/python -m pytest apps/catalog/tests/test_models.py -q`: falló
  antes de ejecutar la aserción con `ProgrammingError` porque la tabla
  `catalog_category` no existe en PostgreSQL.
- El fallo no valida ni refuta D-CAT-01: confirma que falta la migración inicial
  de `catalog`.
- No se generó ni aplicó una migración, ya que requiere autorización específica
  y la revisión de los cambios generados.
- No se añadieron modelos de suscripción, compra, pedido ni stock.
- No se creó ningún commit.

## 2026-08-21 — Migración inicial del catálogo en PostgreSQL

### Objetivo y alcance

Aplicar la migración inicial de `apps.catalog` autorizada por el responsable
del proyecto para crear las tablas necesarias del modelo de catálogo en
PostgreSQL. El alcance se limita a la estructura persistente de `Category`,
`Product`, `LicenseType` y `ProductLicenseOffer` y a la prueba de la decisión
D-CAT-01.

### Revisión de migración

- Se confirmó que `AUTH_USER_MODEL` continúa siendo `users.User` antes de la
  operación.
- La prueba de catálogo estuvo en Red antes de aplicar la migración porque
  `catalog_category` no existía.
- `catalog.0001_initial` ya estaba presente en el árbol de trabajo; Django no
  detectó cambios adicionales al ejecutar `makemigrations catalog`.
- Se revisó `migrate catalog --plan`: crea exclusivamente `Category`,
  `LicenseType`, `Product` y `ProductLicenseOffer`.
- La migración contiene las restricciones de SKU y slugs únicos, una oferta por
  producto y licencia, precio no negativo y relaciones `PROTECT`.

### Resultado y comprobaciones

- `.venv/bin/python manage.py migrate catalog`: aplicada correctamente en
  PostgreSQL.
- `.venv/bin/python manage.py showmigrations catalog`: `0001_initial` aplicada.
- La prueba focalizada pasó: `1 passed`.
- Puerta de calidad: `manage.py check --database default`, comprobaciones de
  migración, suite completa (`7 passed`), Ruff, formato, `pip check` y
  `git diff --check`, correctos.
- Se eliminaron imports vacíos de los stubs de `admin.py` y `views.py`. Las
  listas requeridas por las opciones `Meta` de Django mantienen su forma para
  no introducir una migración de opciones; se limitaron las excepciones Ruff a
  esas declaraciones.

### Alcance excluido

- No se implementaron catálogo web, API, Django Admin funcional, compra,
  pedido, pago, licencia, descarga, suscripciones ni stock.
- D-CAT-02 y las demás decisiones pendientes continúan sin aprobarse.
- No se creó ningún commit.

## 2026-08-21 — Revisión de secuencia y patrón de implementación del catálogo

### Resultado de la revisión

Se documentó que la aprobación de RF-01, RF-02, RF-03, RF-12 y RF-15 fue una
precondición necesaria, pero no suficiente para crear el modelo del catálogo.
`ProductLicenseOffer` y su prueba de precios específicos codifican la separación
entre producto, licencia y precio propuesta en D-CAT-02, que continúa pendiente
de aprobación.

La primera ejecución de la prueba no fue un Red válido de negocio: falló porque
no existía la tabla `catalog_category`. Tras revisar y aplicar
`catalog.0001_initial` en PostgreSQL, la prueba pasó. El resultado demuestra la
persistencia de ofertas producto-licencia, no la implementación completa de los
requisitos de catálogo ni una compra histórica de RF-06.

### Patrón acordado

Para cualquier incremento posterior: requisito y criterio aprobados, decisiones
que se codificarán aprobadas, prueba Red por ausencia de comportamiento,
implementación mínima, migración generada y revisada, Green, regresión y
evidencia real. La guía de entrevista recoge esta conclusión para su defensa.

## 2026-08-25 — Aprobación del checkpoint del catálogo v0.2.0

### Decisiones aprobadas

Por confirmación explícita de `acarras93-alt`, propietario del repositorio, se
cerraron las decisiones de producto necesarias para iniciar el desarrollo
test-first del catálogo:

- D-CAT-02 separa producto, tipo de licencia y oferta; el precio pertenece a la
  oferta.
- D-CAT-03 adopta inicialmente YouTube y redes sociales como una licencia
  conjunta, producción cinematográfica y publicidad, cargadas como datos.
- D-CAT-04 conserva duración en milisegundos, WAV/FLAC/AIFF, frecuencias
  iniciales de 44100/48000/96000 Hz y profundidades de 16/24/32 bits. La fixture
  de demostración partirá de WAV, 48000 Hz y 24 bits.
- D-CAT-05 define una preview MP3 independiente, con marca audible, duración
  máxima de 30 segundos y sin fallback al archivo maestro.
- D-CAT-06 aprueba la separación entre almacenamiento público y privado; la
  entrega autorizada concreta se definirá antes de RF-11.
- D-CAT-07 fija rutas web y API, paginación de 12, orden estable y respuestas
  200, 400 y 404.
- D-CAT-08 elige una fixture ficticia y reproducible para las evidencias de
  v0.2.0. RF-15 permanece íntegramente planificado para v0.9.0 y las pruebas no
  dependerán de la fixture.
- D-CAT-09 aprueba la futura instantánea inmutable de la línea de pedido, cuya
  implementación corresponde a RF-06.

También se cambiaron RNF-08 y RNF-09 de `Propuesto` a `Aprobado`, completando la
puerta documental RNF-06 a RNF-11 exigida por el catálogo.

### Estado técnico y alcance excluido

La aprobación de una decisión no se presenta como implementación. Los modelos
actuales respaldan parcialmente D-CAT-02, D-CAT-04 y D-CAT-05; todavía no
existen selectores públicos, vistas, URLs, templates, serializers, API ni
fixture de demostración. D-CAT-06 y D-CAT-09 conservan explícitamente su
implementación para RF-11 y RF-06, respectivamente.

No se modificaron código, configuración, modelos, migraciones, dependencias,
pruebas ni evidencias. El siguiente incremento autorizado es seleccionar
CA-RF01-01, escribir su prueba Red válida y desarrollar el selector compartido
mínimo.

### Comprobaciones y recuperación del entorno

- El primer intento de `.venv/bin/python -m pytest -q` no pudo conectar con
  PostgreSQL porque Docker Desktop no estaba disponible. El resultado fue
  `4 passed, 1 warning, 3 errors`; los tres errores correspondían a pruebas con
  acceso a base de datos y no constituyeron un estado Red válido de negocio.
- Tras iniciar Docker Desktop, `docker compose up -d db` dejó el contenedor de
  PostgreSQL en estado `healthy` y publicado en el puerto local configurado.
- La repetición de `.venv/bin/python -m pytest -q` finalizó con `7 passed`.
- Se ejecutó la puerta base con `set -e`: comprobaciones de Django y
  migraciones, pytest, Ruff, `pip check`, `git diff --check` y `git status
  --short`. Todos los comandos terminaron correctamente; `pip check` mostró
  únicamente el aviso conocido de permisos de caché.
- RNF-11 conserva el estado `Aprobado`: esta recuperación de entorno no
  verifica los incrementos funcionales, sus evidencias ni su versión Git.
- Se alinearon README, flujos de Copilot, planning, checkpoint, guía de
  entrevista y registro de IA con este estado. Las entradas históricas conservan
  los estados que describían en su fecha original.

### Trabajo pendiente

- Seleccionar CA-RF01-01, escribir su prueba Red válida y desarrollar el
  selector compartido mínimo.
- Crear la fixture ficticia acordada en D-CAT-08 en su incremento propio, sin
  convertirla en dependencia de las pruebas automáticas.

### Versionado del checkpoint

- Tras revisar `git diff` y `git diff --staged`, se creó el commit
  `4b13fd4 feat: add catalog domain models`.
- El commit registra requisitos y decisiones aprobadas, la configuración de la
  app, los modelos de catálogo, `catalog.0001_initial`, su prueba de
  persistencia y la documentación operativa directa.
- La trazabilidad de IA, la bitácora, la guía de entrevista, las instrucciones
  del repositorio y el ajuste de ADR se mantienen en un commit documental
  separado.

## 2026-08-26 — CA-RF01-01: lista pública mínima de catálogo

### Objetivo y alcance

Implementar y verificar CA-RF01-01: un visitante puede abrir `/catalog/` y ver
un producto cuando el producto, su categoría y una oferta de licencia están
activos. El incremento crea una consulta reutilizable de productos disponibles
y una interfaz web mínima que la utiliza.

### Cambios realizados

- Se creó `apps/catalog/selectors.py` con `get_available_products()`, que
  filtra producto, categoría y oferta activos, elimina duplicados y ordena por
  nombre e identificador.
- Se añadieron la vista, las URLs de `apps.catalog`, su inclusión global y una
  plantilla mínima para publicar `/catalog/`.
- Se creó `apps/catalog/tests/test_views.py` con una prueba aislada que prepara
  una categoría, producto y oferta activos y comprueba la respuesta pública.
- Se incorporó `docs/evidence/RF-01/CA-RF01-01.md` con los resultados reales
  del ciclo Red-Green y de la puerta de calidad.

### Comprobaciones ejecutadas

- RED válido: la prueba focalizada falló con `404` para `/catalog/` mientras
  PostgreSQL y las siete pruebas preexistentes funcionaban correctamente.
- GREEN: `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`
  finalizó con `1 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, suite completa
  (`8 passed`), Ruff, `pip check` y `git diff --check` correctos.

### Incidencia de proceso

La integración HTTP (vista, URLs, inclusión global y plantilla) se añadió antes
de recibir autorización específica para ese cambio. Tras la revisión del diff,
el responsable aprobó expresamente conservarla como implementación mínima de
CA-RF01-01. La incidencia se registra para mantener trazabilidad del flujo de
autorización; no modifica los resultados observados de las pruebas.

### Alcance excluido

No se implementaron filtros, paginación, precio mínimo, detalle, API, fixture
de demostración, modelos, migraciones ni dependencias. El cambio preexistente
en `docs/requirements/functional-requirements.md` no forma parte de este
incremento.

## 2026-08-26 — CA-RF01-02: exclusión de producto inactivo

### Objetivo y resultado

Se añadió cobertura HTTP para CA-RF01-02: un producto inactivo, con categoría
y oferta de licencia activas, no aparece al consultar `/catalog/`.

La prueba pasó en su primera ejecución porque
`get_available_products()` ya filtraba `Product.is_active=True`. Se registra
como cobertura añadida de comportamiento preexistente, no como un nuevo ciclo
RED-GREEN ni como un cambio de producción.

### Comprobaciones ejecutadas

- `.venv/bin/ruff format apps/catalog/tests/test_views.py`: sin cambios.
- `.venv/bin/ruff check apps/catalog/tests/test_views.py`: correcto.
- `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`: `2 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, suite completa
  (`9 passed`), Ruff, `pip check` y `git diff --check` correctos.

### Alcance excluido

No se modificaron selector, vista, URLs, plantilla, modelos, migraciones,
dependencias ni documentación de requisitos. Los criterios restantes de RF-01
continúan pendientes.

## 2026-08-26 — CA-RF01-03: estado vacío del catálogo

### Objetivo y alcance

Implementar y verificar CA-RF01-03: cuando no hay productos disponibles, un
visitante que abre `/catalog/` recibe una respuesta correcta y un mensaje de
estado vacío comprensible.

### Cambios realizados

- Se añadió una prueba HTTP aislada en `apps/catalog/tests/test_views.py` que
  consulta un catálogo vacío y comprueba el estado `200` y el mensaje visible.
- Se actualizó `apps/catalog/templates/catalog/product_list.html` con el bloque
  `{% empty %}` y el texto `No hay productos disponibles en este momento.`.
- Se creó `docs/evidence/RF-01/CA-RF01-03.md` con el ciclo Red-Green y los
  resultados verificados.
- Se actualizó el resumen de estado de `README.md`.

### Comprobaciones ejecutadas

- RED válido: Ruff fue correcto y la prueba focalizada finalizó con
  `1 failed, 2 passed`; `/catalog/` respondió `200`, pero la lista vacía no
  mostraba el mensaje requerido.
- GREEN: `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`
  finalizó con `3 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, suite completa
  (`10 passed`), Ruff, `pip check` y `git diff --check` correctos.

### Resultado y alcance excluido

El catálogo comunica su estado vacío sin error HTTP. No se modificaron el
selector, la vista, las URLs, los modelos, las migraciones ni dependencias. No
se implementaron filtros, paginación, precio mínimo, detalle, API, consultas
N+1 ni los demás criterios pendientes de RF-01. El cambio preexistente de
formato en `docs/requirements/functional-requirements.md` no forma parte de
este incremento.

## 2026-08-27 — CA-RF01-04: paginación del catálogo

### Objetivo y alcance

Implementar y verificar CA-RF01-04: el catálogo público divide los productos
disponibles en bloques de 12 y permite al visitante cambiar entre páginas
existentes. Se verificó además FE-01, que exige un `404` para páginas
inexistentes o inválidas.

### Cambios realizados

- Se actualizó `apps/catalog/views.py` para paginar el selector de productos
  disponibles con `Paginator` y 12 elementos por página.
- La vista usa `Paginator.page()` con página `1` por defecto y transforma
  `EmptyPage` y `PageNotAnInteger` en `Http404`.
- Se actualizó `apps/catalog/templates/catalog/product_list.html` con enlaces
  condicionales anterior y siguiente hacia páginas existentes.
- Se amplió `apps/catalog/tests/test_views.py` con preparación reutilizable y
  pruebas HTTP para la segunda página, enlaces y páginas inválidas.
- Se creó `docs/evidence/RF-01/CA-RF01-04.md` y se actualizó el resumen de
  estado de `README.md`.

### Comprobaciones ejecutadas

- RED de segunda página: `1 failed, 3 passed`; la vista ignoraba `page` y
  devolvía los 13 productos.
- RED de navegación: `1 failed, 4 passed`; la plantilla no contenía los enlaces
  de paginación.
- RED de FE-01: `3 failed, 5 passed`; `Paginator.get_page()` respondía `200`
  para página inexistente, no numérica o menor que uno.
- GREEN focalizado: `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`
  finalizó con `8 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, suite completa
  (`15 passed`), Ruff, `pip check` y `git diff --check` correctos.

### Resultado y alcance excluido

La página pública del catálogo permite navegar entre páginas existentes y
responde `404` ante páginas inválidas o inexistentes. No se modificaron el
selector, los modelos, las migraciones ni dependencias. No se implementaron
filtros, ordenación, precio mínimo, detalle, API, consultas N+1 ni conservación
de parámetros de consulta, que pertenece a RF-03.

## 2026-08-27 — CA-RF01-06: precio mínimo de las ofertas activas

### Objetivo y alcance

Implementar y verificar CA-RF01-06: la tarjeta de un producto con varias
ofertas activas muestra el precio mínimo sin ambigüedad.

### Cambios realizados

- Se amplió `get_available_products()` con la anotación `minimum_price`, que
  calcula el mínimo exclusivamente entre las ofertas activas.
- La plantilla de catálogo muestra `Desde <precio> EUR` en cada tarjeta y
  desactiva la localización del importe para conservar el separador decimal
  definido por el criterio.
- Se añadió una prueba HTTP con dos ofertas activas, de `12.90 EUR` y
  `29.90 EUR`, que comprueba que solo aparece el precio menor.
- Se actualizó el plan de pruebas y se creó la evidencia del criterio.

### Comprobaciones ejecutadas

- RED válido: Ruff fue correcto y la prueba focalizada finalizó con
  `1 failed, 8 passed`; `/catalog/` devolvió `200` y mostró el producto, pero
  no contenía `Desde 12.90 EUR`.
- La primera comprobación tras implementar el cálculo mostró `12,90 EUR` por
  la localización de Django. Se corrigió la representación con `unlocalize` y
  la prueba focalizada finalizó con `9 passed`.
- Regresión: `.venv/bin/python -m pytest -q` finalizó con `16 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, Ruff, `pip check`
  y `git diff --check` correctos; Ruff informó de 59 archivos ya formateados.

### Resultado y alcance excluido

La tarjeta pública comunica el precio mínimo de las ofertas activas como
`Desde <precio> EUR`. No se implementaron filtros, ordenación, detalle, API,
consultas N+1, cambios de moneda, archivos privados ni los demás criterios
pendientes de RF-01.

## 2026-08-27 — CA-RF01-07: carga eficiente de relaciones del catálogo

### Objetivo y alcance

Implementar y verificar CA-RF01-07: cargar categorías y ofertas activas de los
productos disponibles sin añadir una consulta por cada producto de la página.

### Cambios realizados

- Se creó una prueba de integración de PostgreSQL para el selector que compara
  la carga de un producto frente a doce y accede de forma explícita a categoría
  y ofertas activas.
- `get_available_products()` carga la categoría con `select_related()` y
  precarga exclusivamente ofertas activas con `Prefetch`.
- Se actualizó la trazabilidad del requisito, el README y la evidencia del
  criterio.

### Comprobaciones ejecutadas

- RED válido: la prueba focalizada finalizó con `1 failed`; al acceder a las
  relaciones, el conteo aumentó de 3 consultas para un producto a 25 para doce.
- GREEN: la prueba de selectores finalizó con `1 passed` y las pruebas HTTP de
  catálogo con `9 passed`.
- Medición posterior con PostgreSQL, en una transacción revertida: un producto
  y doce productos requirieron 2 consultas cada uno.
- Regresión: `.venv/bin/python -m pytest -q` finalizó con `17 passed`.
- Puerta de calidad: comprobaciones de Django y migraciones, Ruff, `pip check`
  y `git diff --check` correctos; Ruff informó de 61 archivos ya formateados.

### Resultado y alcance excluido

El selector evita N+1 al cargar categorías y ofertas activas. No se
implementaron filtros, ordenación, detalle, API, cambios de moneda, archivos
privados ni los demás criterios pendientes de RF-01.

## 2026-08-27 — CA-RF02-01: detalle público de producto disponible

### Objetivo y alcance

Implementar y verificar CA-RF02-01: un visitante puede consultar el detalle de
un producto disponible y ver sus metadatos técnicos y sus ofertas de licencia
activas. GitHub Copilot se utilizó para crear la prueba RED, implementar el
detalle mínimo y actualizar esta trazabilidad.

### Cambios realizados

- Se añadió una prueba HTTP aislada para `GET /catalog/nocturnos-urbanos/` con
  categoría, producto, tipo de licencia y oferta activos.
- Se registró la ruta `/catalog/<slug>/` y una vista pública que resuelve el
  producto mediante `get_available_products()`; los productos no disponibles
  conservan la respuesta 404 del helper de Django.
- Se creó la plantilla de detalle con nombre, categoría, descripción, duración,
  formato, frecuencia, profundidad y datos públicos de cada oferta activa.
- No se modificaron modelos, selector, migraciones, dependencias ni
  configuración de PostgreSQL.

### Comprobaciones ejecutadas

- RED válido: `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_displays_technical_metadata_and_active_license_offer
  -q` falló con `assert 404 == 200`, porque aún no existía la ruta de detalle.
- GREEN: el mismo comando finalizó con `1 passed in 0.45s`.
- Puerta de calidad: `manage.py check --database default`,
  `makemigrations --check --dry-run`, `migrate --check`, Ruff, `pip check` y
  `git diff --check` fueron correctos; `.venv/bin/python -m pytest -q`
  finalizó con `18 passed in 0.94s`.

### Resultado y alcance excluido

El detalle público reutiliza la misma definición de disponibilidad que el
catálogo y muestra la representación mínima de CA-RF02-01. Permanecen
pendientes preview y reproductor, comprobaciones específicas de productos no
disponibles, exclusión explícita de ofertas inactivas, ausencia de preview y
privacidad del archivo maestro. No se generaron evidencias visuales ni se creó
ningún commit.

## 2026-08-27 — CA-RF02-03: detalle no disponible o inexistente

### Objetivo y alcance

Verificar CA-RF02-03 para los casos de un producto inactivo y de un slug que
no existe. El comportamiento se incorporó como cobertura de la vista de
detalle existente, no como una nueva implementación de producción.

### Cambios realizados

- Se añadieron dos pruebas HTTP aisladas en
  `apps/catalog/tests/test_views.py`: una crea un producto inactivo con
  categoría y oferta activas, y otra solicita un slug sin datos creados.
- Ambas prueban que el detalle responde `404`.
- No se modificaron vista, selector, URLs, modelos, migraciones, dependencias
  ni configuración.

### Comprobaciones ejecutadas

- `.venv/bin/ruff format apps/catalog/tests/test_views.py`: un archivo sin
  cambios.
- `.venv/bin/ruff check apps/catalog/tests/test_views.py`: correcto.
- `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`: `11 passed
  in 0.65s`.
- `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_returns_404_for_an_unknown_slug
  -q`: `1 passed in 0.43s`.
- Puerta de calidad: comprobaciones Django y migraciones, Ruff, `pip check` y
  `git diff --check` correctos; `.venv/bin/python -m pytest -q` finalizó con
  `19 passed in 1.02s`.

### Resultado y alcance excluido

CA-RF02-03 queda cubierto como comportamiento preexistente: la vista usa
`get_object_or_404()` sobre `get_available_products()`, que excluye productos
inactivos y no encuentra slugs inexistentes. No se implementaron preview,
reproductor, exclusión específica de ofertas inactivas, ausencia de preview ni
privacidad del archivo maestro.

## 2026-08-27 — CA-RF02-03: casos adicionales de producto no disponible

### Objetivo y alcance

Ampliar la cobertura de CA-RF02-03 para una categoría inactiva y para un
producto que no tiene ninguna oferta activa. Ambos casos pertenecen a la misma
definición de disponibilidad pública del detalle.

### Cambios realizados

- Se añadieron dos pruebas HTTP aisladas en `apps/catalog/tests/test_views.py`.
- La primera mantiene producto y oferta activos con categoría inactiva; la
  segunda mantiene producto y categoría activos con una oferta inactiva.
- No se modificaron producción, migraciones, dependencias ni configuración.

### Comprobación ejecutada

- `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_returns_404_for_an_inactive_category
  apps/catalog/tests/test_views.py::test_product_detail_returns_404_without_an_active_license_offer
  -q`: `2 passed in 0.48s`.

### Resultado y alcance excluido

Los dos casos pasan como comportamiento preexistente del selector compartido.
No se implementaron preview, reproductor, exclusión de una oferta inactiva
cuando existan otras activas, ausencia de preview ni privacidad del maestro.

## 2026-08-27 — CA-RF02-04: exclusión de oferta inactiva en el detalle

### Objetivo y alcance

Verificar CA-RF02-04: cuando un producto disponible tiene una oferta de
licencia activa y otra inactiva, el detalle público solo representa la activa.

### Cambios realizados

- Se añadió una prueba HTTP aislada en `apps/catalog/tests/test_views.py` con
  dos tipos de licencia y sus ofertas correspondientes.
- La prueba comprueba `200`, la presencia de la licencia activa y la ausencia
  de la licencia vinculada a la oferta inactiva.
- No se modificaron selector, vista, URL, plantilla, modelos, migraciones,
  dependencias ni configuración.

### Comprobaciones ejecutadas

- `.venv/bin/ruff format apps/catalog/tests/test_views.py`: un archivo sin
  cambios.
- `.venv/bin/ruff check apps/catalog/tests/test_views.py`: correcto.
- `.venv/bin/python -m pytest apps/catalog/tests/test_views.py -q`: `15 passed
  in 0.69s`.
- Puerta de calidad: comprobaciones Django y migraciones, Ruff, `pip check` y
  `git diff --check` correctos; `.venv/bin/python -m pytest -q` finalizó con
  `23 passed in 1.03s`.

### Resultado y alcance excluido

CA-RF02-04 queda cubierto como comportamiento preexistente: el prefetch del
selector compartido solo incluye `ProductLicenseOffer` activas. No se
implementaron preview, reproductor, control de productos no disponibles,
ausencia de preview ni privacidad del archivo maestro.

## 2026-08-27 — CA-RF02-05: aviso parcial de preview ausente

### Objetivo y alcance

Implementar la parte visible de CA-RF02-05: si un producto disponible no tiene
`preview_file` configurado, el detalle público sigue respondiendo y muestra el
aviso `Preview no disponible.`.

### Cambios realizados

- Se añadió una prueba HTTP aislada en `apps/catalog/tests/test_views.py` con
  producto, categoría y oferta activos, pero sin preview configurada.
- Se actualizó `apps/catalog/templates/catalog/product_detail.html` para
  mostrar el aviso solo cuando `preview_file` está vacío.
- No se modificaron modelos, migraciones, dependencias, configuración ni
  almacenamiento.

### Comprobaciones ejecutadas

- RED: `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_displays_a_message_when_preview_is_unavailable
  -q` falló porque el HTML no contenía `Preview no disponible.`.
- GREEN: el mismo comando finalizó con `1 passed in 0.44s` después de añadir el
  aviso.
- Puerta de calidad: `.venv/bin/python -m pytest -q` finalizó con `24 passed in
  1.01s`; comprobaciones Django y migraciones, Ruff, `pip check` y
  `git diff --check` correctos.

### Resultado y alcance excluido

El detalle comunica la indisponibilidad de la preview configurada sin alterar
la disponibilidad del producto. CA-RF02-05 no se declara cerrado: queda por
verificar que el archivo maestro no se usa ni se expone. No se implementaron
reproductor, almacenamiento, archivo maestro ni otros criterios.

## 2026-08-28 — Contrato mínimo de almacenamiento público y privado

### Objetivo y decisión aprobada

Concretar D-CAT-06 y RNF-06 sin implementar todavía el archivo maestro. Se
aprobó que `Product.preview_file` y el futuro `Product.master_file` utilicen
almacenamientos explícitos con raíces físicas distintas. Solo las previews
podrán disponer de URL pública en desarrollo; el almacenamiento privado no
generará URL y deberá fallar sin revelar el nombre ni la ruta del maestro.

`Product.master_file` representará una única clave interna y admitirá un valor
vacío hasta que RF-11 defina su obligatoriedad. Las interfaces públicas no
recibirán el campo ni sus datos derivados, y la ausencia o fallo de preview
nunca habilitará el maestro como alternativa.

### División del trabajo futuro

La aprobación no autoriza una implementación conjunta. Los incrementos se
realizarán por separado y requerirán su propio ciclo Red-Green y aprobación de
alcance:

1. persistencia de `master_file` y separación de los almacenamientos;
2. CA-RF02-05, ausencia o fallo de preview sin fallback al maestro;
3. CA-RF02-06, exclusión del maestro en HTML y contexto público;
4. entrega autorizada en RF-11.

### Comprobaciones y alcance excluido

Se revisaron D-CAT-06, RNF-06, RF-02, el estado propuesto de RF-11 y el código y
configuración actuales antes de aprobar el contrato. Este cambio es
exclusivamente documental: no se modificaron código, pruebas, configuración,
migraciones ni dependencias, y no se ejecutaron pruebas automáticas.

La vista de descarga, la respuesta del archivo, los permisos y las
comprobaciones de usuario, pedido, licencia y autorización permanecen fuera de
alcance hasta que RF-11 y sus criterios sean aprobados.

## 2026-08-28 — Persistencia y almacenamiento privado de `master_file`

### Objetivo y requisito relacionado

Implementar exclusivamente el primer incremento aprobado de D-CAT-06 y RNF-06:
persistir una clave opcional en `Product.master_file`, separar físicamente el
almacenamiento de previews y maestros, y evitar que el almacenamiento privado
genere una URL pública. La asistencia utilizada fue GitHub Copilot.

### Cambios realizados

- Se añadieron `PreviewStorage` y `PrivateMasterStorage` con raíces distintas.
- `PrivateMasterStorage.url()` lanza `NotImplementedError` con un mensaje
  constante que no contiene el nombre ni la ruta solicitados.
- `Product.preview_file` utiliza el almacenamiento público explícito.
- `Product.master_file` utiliza el almacenamiento privado, admite un valor
  vacío mediante `blank=True` y no utiliza `null=True`.
- Django generó la migración
  `catalog.0002_product_master_file_alter_product_preview_file`, con una
  operación `AddField` y una operación `AlterField`.

### Comprobaciones ejecutadas

- RED: `.venv/bin/python -m pytest
  apps/catalog/tests/test_models.py::test_product_master_file_uses_private_storage_without_a_public_url
  -q` falló con `TypeError: Product() got unexpected keyword arguments:
  'master_file'` antes de implementar el campo.
- GREEN: la misma prueba finalizó con `1 passed in 0.36s` después de implementar
  el contrato y generar la migración.
- `.venv/bin/python manage.py makemigrations catalog --check --dry-run`: `No
  changes detected in app 'catalog'`.
- El plan de migración mostró únicamente
  `catalog.0002_product_master_file_alter_product_preview_file`, con
  `Add field master_file to product` y `Alter field preview_file on product`.
- La migración se aplicó por nombre exacto con resultado `OK`; `showmigrations
  catalog` confirmó `0001_initial` y `0002` aplicadas.
- `.venv/bin/python manage.py check --database default`: sin incidencias.
- Comprobación de migraciones: sin cambios ni migraciones pendientes.
- `.venv/bin/python -m pytest -q`: `25 passed in 1.06s`.
- `.venv/bin/ruff check .`: detectó inicialmente dos errores locales; después
  de corregirlos finalizó con `All checks passed!`.
- `.venv/bin/ruff format --check .`: `67 files already formatted`.
- `.venv/bin/pip check`: `No broken requirements found`.
- `git diff --check`: correcto, sin salida.

### Resultado y alcance excluido

El primer incremento de D-CAT-06 queda implementado y comprobado: la clave del
maestro persiste, previews y maestros usan raíces distintas, y solicitar la URL
privada falla sin revelar la clave. No se creó ninguna ruta pública para el
maestro.

CA-RF02-05 y CA-RF02-06 no se declaran verificados. No se implementaron cambios
en URLs, vistas, templates, selectores ni la entrega autorizada; RF-11 conserva
su estado propuesto. No se creó ningún commit.

## 2026-08-28 — Verificación de CA-RF02-05 con almacenamiento privado

### Objetivo y requisito relacionado

Completar la verificación de CA-RF02-05 sobre el contrato mínimo aprobado de
D-CAT-06 y RNF-06. La asistencia utilizada fue GitHub Copilot.

La prueba aprobada crea un producto disponible con `preview_file` vacío y una
clave de maestro identificable. Comprueba que la clave persiste, que preview y
maestro usan raíces distintas y que solicitar la URL privada lanza
`NotImplementedError` sin revelar el nombre del maestro. También comprueba que
el detalle responde 200, muestra `Preview no disponible.` y no contiene la
clave ni el nombre del maestro en el HTML.

### Resultado test-first y comprobaciones ejecutadas

- La nueva prueba no produjo un estado Red: su primera ejecución finalizó con
  `1 passed in 0.48s` porque los incrementos previos ya proporcionaban el
  comportamiento observable y el almacenamiento requerido. Se clasificó como
  Green preexistente, no como fallo de entorno o configuración.
- Tras corregir únicamente el estilo de la prueba, `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_without_preview_never_exposes_the_private_master
  -q` finalizó con `1 passed in 0.48s`.
- `.venv/bin/python manage.py makemigrations catalog --check --dry-run` indicó
  `No changes detected in app 'catalog'`.
- La migración `catalog.0002_product_master_file_alter_product_preview_file` se
  revisó sin editarla: contiene solo `AddField` para `master_file` y
  `AlterField` para `preview_file`, sin valores por defecto, migraciones de
  datos ni cambios ajenos.
- El plan por nombre exacto no mostró operaciones pendientes y
  `showmigrations catalog` confirmó `0001_initial` y `0002` aplicadas. Durante
  esta verificación no se aplicó ninguna migración.
- `.venv/bin/python manage.py check --database default` finalizó sin
  incidencias y la comprobación de migraciones no detectó cambios ni
  migraciones pendientes.
- `.venv/bin/python -m pytest -q` finalizó con `26 passed in 1.06s`.
- La primera puerta global de Ruff detectó `B018` y un cambio de formato en la
  prueba nueva. Después de corregir solo esas dos incidencias,
  `.venv/bin/ruff check .` finalizó con `All checks passed!` y
  `.venv/bin/ruff format --check .` con `67 files already formatted`.
- `.venv/bin/pip check` indicó `No broken requirements found` y
  `git diff --check` finalizó correctamente sin salida.

### Resultado y alcance excluido

CA-RF02-05 queda verificado: ante una preview ausente, el detalle permanece
consultable, informa de la indisponibilidad y no usa ni revela el archivo
maestro en el HTML. El almacenamiento privado tampoco proporciona una URL ni
revela la clave solicitada en el error.

CA-RF02-06 permanece pendiente porque exige revisar de forma independiente
todo el HTML y el contexto público. También permanecen fuera de alcance el
reproductor de CA-RF02-02, la API, la entrega autorizada, los permisos de
descarga y RF-11. No se creó ningún commit.

## 2026-08-28 — Verificación de CA-RF02-06 en HTML y contexto público

### Objetivo y requisito relacionado

Verificar CA-RF02-06 sobre el almacenamiento privado aprobado en D-CAT-06 y
RNF-06. Ante un producto con una clave de maestro identificable, ni el HTML ni
el contexto público del detalle deben permitir obtener su nombre, ruta o URL.
La asistencia utilizada fue GitHub Copilot.

### Cambios realizados

- Se añadió una prueba HTTP aislada que inspecciona el HTML y los contextos
  renderizados por Django.
- La vista de detalle dejó de entregar objetos ORM al contexto y construye una
  proyección explícita con los metadatos públicos del producto y sus ofertas.
- El template consume esa proyección pública y conserva el contenido observable
  del detalle.
- No se modificaron URLs, selectores, modelos, almacenamiento, configuración ni
  migraciones.

### Ciclo Red-Green y comprobaciones ejecutadas

- La primera ejecución de la prueba falló por una preparación incorrecta al
  intentar usar `flatten()` directamente sobre `ContextList`; se corrigió solo
  la prueba y ese resultado no se consideró un Red funcional.
- RED válido: `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_product_detail_context_excludes_the_private_master
  -q` finalizó con `1 failed in 0.52s`. El contexto incluía el objeto
  `Product`, que permitía acceder a `master_file`.
- GREEN: el mismo nodo finalizó inicialmente con `1 passed in 0.44s` y su
  comprobación final con `1 passed in 0.43s`.
- Regresión focalizada: `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py -q` finalizó con `18 passed in 0.66s`.
- Regresión completa: `.venv/bin/python -m pytest -q` finalizó con `27 passed
  in 1.11s`, sin pruebas fallidas ni errores.
- `.venv/bin/python manage.py check --database default` finalizó sin
  incidencias.
- `.venv/bin/python manage.py makemigrations --check --dry-run` indicó `No
  changes detected` y `.venv/bin/python manage.py migrate --check` confirmó que
  no había migraciones pendientes.
- `.venv/bin/ruff check .` finalizó con `All checks passed!` y
  `.venv/bin/ruff format --check .` con `67 files already formatted`.
- `.venv/bin/pip check` indicó `No broken requirements found` y
  `git diff --check` finalizó correctamente sin salida.

### Resultado y alcance excluido

CA-RF02-06 queda verificado. El contexto del detalle contiene únicamente una
proyección de datos públicos y el HTML no contiene la clave, el nombre, la ruta
ni una URL del maestro. El almacenamiento privado conserva el aislamiento
verificado en el incremento anterior.

Permanecen fuera de alcance CA-RF02-02, la API, la entrega autorizada, los
permisos de descarga y RF-11. No se generaron ni aplicaron migraciones y no se
creó ningún commit.

## 2026-08-28 — Preview pública y aceptación integrada de RF-02

### Objetivo y requisito relacionado

Completar CA-RF02-02 y comprobar en una única prueba de aceptación el recorrido
público de RF-02 con el cliente HTTP de Django y PostgreSQL. La asistencia
utilizada fue GitHub Copilot.

### Cambios realizados

- La proyección pública del detalle incluye únicamente la URL generada por el
  almacenamiento de previews cuando existe un archivo promocional.
- El template muestra un reproductor HTML `audio` con esa URL pública y conserva
  el aviso `Preview no disponible.` cuando falta la preview.
- Se añadió una prueba de aceptación para un visitante anónimo que consulta el
  catálogo, abre el detalle, recibe metadatos y ofertas activas, excluye ofertas
  inactivas y comprueba la preview pública y la privacidad del maestro en HTML
  y contexto.
- No se modificaron URLs, selectores, modelos, configuración, almacenamiento ni
  migraciones y no se añadieron dependencias.

### Ciclo Red-Green y comprobaciones ejecutadas

- RED: `.venv/bin/python -m pytest
  apps/catalog/tests/test_views.py::test_anonymous_visitor_can_browse_the_public_product_flow_safely
  -q` finalizó con `1 failed in 0.59s`. El catálogo, el detalle, los metadatos,
  las ofertas y la privacidad pasaban, pero el HTML no contenía
  `/media/previews/rf02-public-preview.mp3`.
- GREEN: el mismo nodo finalizó con `1 passed in 0.45s` después de añadir la URL
  pública al contexto seguro y el reproductor al template.
- Puerta posterior observada: `.venv/bin/python manage.py check --database
  default` finalizó sin incidencias; `.venv/bin/python -m pytest -q` finalizó
  con `28 passed in 1.04s`; `.venv/bin/ruff check .` finalizó con `All checks
  passed!`; y `.venv/bin/ruff format --check .` indicó `67 files already
  formatted`.

### Resultado y alcance excluido

CA-RF02-02 queda verificado: el detalle de un producto con preview referencia
exclusivamente la URL del archivo promocional público. La aceptación integrada
confirma además el recorrido catálogo-detalle y mantiene el nombre, la ruta y
la URL del maestro fuera del HTML y del contexto.

La preparación manual del MP3, su marca audible y su duración máxima no se
validan dentro de Django. También permanecen fuera de alcance la API, la
entrega autorizada, los permisos de descarga y RF-11. No se creó ningún commit.

## 2026-08-28 — Entrega HTTP de previews y cierre de CA-RF02-02

### Objetivo y requisito relacionado

Completar la comprobación observable de CA-RF02-02: no solo publicar la URL en
el HTML, sino permitir que un visitante anónimo obtenga mediante GET los bytes
del archivo promocional, manteniendo el maestro en almacenamiento privado. La
asistencia utilizada fue GitHub Copilot.

### Cambios realizados

- Se declararon `MEDIA_ROOT` y `MEDIA_URL` para la raíz pública de previews.
- El URLconf sirve esa raíz únicamente cuando `DEBUG=True`; `private_media` no
  forma parte de las rutas públicas.
- La prueba específica guarda bytes MP3 ficticios en almacenamiento temporal,
  solicita `preview_file.url`, comprueba respuesta 200 y contenido exacto, y
  elimina el archivo temporal.
- La prueba recarga y restaura el URLconf para no depender del orden de la
  suite. No se modificaron modelos, migraciones ni dependencias.

### Ciclo Red-Green y comprobaciones ejecutadas

- RED válido: la prueba específica finalizó con `1 failed in 0.16s`; el GET a
  `/media/previews/ca-rf02-02-public-preview.mp3` devolvió 404 porque la ruta
  pública aún no estaba registrada.
- GREEN específico: `.venv/bin/python -m pytest -q
  apps/catalog/tests/test_views.py::test_anonymous_visitor_receives_the_public_preview_file`
  finalizó con `1 passed in 0.05s`.
- Regresión final: `.venv/bin/python -m pytest -q` finalizó con `29 passed in
  1.08s` después de corregir el aislamiento del URLconf de la prueba.
- La aceptación vertical preexistente de RF-02 finalizó con `1 passed in
  0.45s` y mantuvo nombre, ruta y URL del maestro fuera del HTML y del contexto.
- `.venv/bin/python manage.py check --database default` no detectó incidencias;
  `.venv/bin/python manage.py makemigrations --check --dry-run` indicó `No
  changes detected`; y `.venv/bin/python manage.py migrate --check` finalizó
  correctamente sin migraciones pendientes ni aplicadas.
- `.venv/bin/ruff check .` finalizó con `All checks passed!`;
  `.venv/bin/ruff format --check .` indicó `67 files already formatted`;
  `.venv/bin/pip check` indicó `No broken requirements found`; y `git diff
  --check` no detectó errores de whitespace.

### Resultado y alcance excluido

CA-RF02-02 queda verificado mediante una entrega HTTP real en desarrollo. La
preview pública y el maestro conservan raíces distintas, y el almacenamiento
privado continúa sin proporcionar URL pública. Permanecen fuera de alcance el
servicio de medios en producción, la entrega autorizada de RF-11, la API y la
validación automática de la preparación, marca audible y duración del MP3. No
se generaron ni aplicaron migraciones y no se creó ningún commit.

## 2026-09-01 — Cierre de decisiones y alcance previo de RF-03

### Objetivo y referencia de producto

Resolver las contradicciones detectadas antes del primer ciclo test-first de
RF-03 sin implementar búsqueda, filtros, ordenación ni conservación de
parámetros. Se inspeccionó la página pública de efectos de sonido de Epidemic
Sound únicamente como referencia: organiza el descubrimiento mediante
categorías visibles y representa cada sonido mediante un título descriptivo,
duración y categoría. No se copiaron marca, contenido, diseño ni el modelo de
suscripción del tercero.

### Decisiones aprobadas

- RF-03 implementará la web; RF-12 añadirá después la interfaz DRF sobre el
  selector compartido.
- `q` buscará la frase normalizada en `name`, `summary` y `description`.
- v0.2.0 filtrará por categoría y licencia; los filtros técnicos quedan
  diferidos porque no están exigidos por los criterios aprobados.
- Una oferta pública exige que tanto la oferta como su tipo de licencia estén
  activos.
- El precio `Desde` seguirá siendo el mínimo global de ofertas públicas aunque
  el catálogo esté filtrado por una licencia concreta.
- Los parámetros conocidos inválidos producirán 400. Los desconocidos se
  ignorarán y no se propagarán a enlaces ni expresiones ORM.
- CA-RF03-07 se clasifica como Green preexistente de RF-01, con implementación
  en `c8e2a20`; no se fabricará un Red.

Las decisiones completas se registraron en
`docs/requirements/rf03-decision-checkpoint.md`. También se completaron las
referencias de commits ya existentes en la trazabilidad de RF-02.

### Verificación y alcance excluido

La regresión específica de las pruebas 404 de paginación finalizó con `3
passed`. Este incremento es documental: no modificó modelos, selector, vistas,
templates, URLs, migraciones ni dependencias. CA-RF03-01 a CA-RF03-06 continúan
sin implementar.

## 2026-09-01 — Disponibilidad pública del tipo de licencia

### Objetivo

Resolver antes de RF-03 una inconsistencia heredada del selector: una oferta
activa asociada a un `LicenseType` inactivo hacía disponible el producto,
abarataba `minimum_price` y se precargaba como oferta pública.

### Ciclo Red-Green

- RED válido: `test_available_products_require_an_active_license_type` finalizó
  con `1 failed`; el selector devolvía un producto cuya única licencia estaba
  inactiva.
- Después de la implementación mínima, la prueba alcanzó la exclusión correcta
  y detectó un error de preparación: la anotación se consultaba en la instancia
  creada, no en la devuelta por el selector. Se corrigió solo esa referencia de
  la prueba.
- GREEN: la prueba específica finalizó con `1 passed`.
- Regresión de selector y vistas: `22 passed`.
- Regresión completa: `30 passed`.
- Ruff sobre los dos archivos modificados finalizó correctamente y confirmó que
  ambos estaban formateados.

### Implementación y alcance

El selector exige `license_type__is_active=True` en disponibilidad, cálculo del
precio mínimo y ofertas precargadas. No se modificaron modelos, migraciones,
vistas, templates, URLs o dependencias. No se implementó ningún criterio de
RF-03. Commit: `3c58ae7`.

## 2026-09-01 — Carga acotada de tipos de licencia

### Objetivo

Cerrar el N+1 heredado antes de RF-03. El selector precargaba ofertas, pero cada
acceso posterior a `offer.license_type` ejecutaba una consulta adicional porque
esa relación no formaba parte del queryset interno del `Prefetch`.

### Ciclo Red-Green

- RED válido: se amplió la prueba de consultas existente para materializar
  `offer.license_type.is_active`. La prueba falló porque las consultas crecieron
  de 3 para un producto a 14 para doce.
- Implementación mínima: el queryset de ofertas añadió
  `select_related("license_type")`.
- GREEN: la prueba focalizada finalizó con `1 passed`.
- Regresión de selector y vistas: `22 passed`.
- Regresión completa: `30 passed`.
- Ruff finalizó correctamente y confirmó el formato de ambos archivos.

### Alcance

El cambio solo completa la carga eficiente del selector compartido para RF-01
y RF-02. No modifica la respuesta, el esquema de datos ni la validación HTTP y
no implementa ningún criterio de RF-03. Commit: `f3991b7`.

## 2026-09-01 — CA-RF03-01: búsqueda textual del catálogo

### Objetivo y ciclo Red-Green

Implementar únicamente la búsqueda pública aprobada por palabra o frase
normalizada en `Product.name`, `Product.summary` y `Product.description`, sin
distinguir mayúsculas de minúsculas y conservando la disponibilidad heredada
de RF-01.

- RED válido: la prueba
  `test_catalog_searches_available_products_by_normalized_text_case_insensitively`
  finalizó con `1 failed in 0.57s`; el producto disponible no coincidente
  `Amanecer rural` apareció porque la vista todavía ignoraba `q`.
- Implementación mínima: `product_list()` normaliza espacios de `q` y entrega
  el valor al selector compartido; `get_available_products()` aplica una
  condición `OR` con `icontains` sobre nombre, resumen y descripción.
- GREEN específico: el mismo nodo finalizó primero con `1 passed in 0.46s` y
  se repitió con `1 passed in 0.46s`.
- Regresión completa: `.venv/bin/python -m pytest -q` finalizó con
  `31 passed in 1.16s`.

### Puerta de calidad y alcance

- `.venv/bin/python manage.py check --database default`: sin incidencias.
- `.venv/bin/python manage.py makemigrations --check --dry-run`: sin cambios.
- `.venv/bin/python manage.py migrate --check`: sin migraciones pendientes.
- `.venv/bin/ruff check .`: todas las comprobaciones superadas.
- `.venv/bin/ruff format --check .`: `70 files already formatted`.
- `.venv/bin/pip check`: ninguna dependencia rota.
- `git diff --check`: sin errores de whitespace.
- `git status --short`: modificados `apps/catalog/selectors.py`,
  `apps/catalog/tests/test_views.py` y `apps/catalog/views.py` antes de esta
  actualización documental.

No se modificaron modelos, migraciones, configuración, URLs, templates,
dependencias ni almacenamiento privado. La suite completa mantuvo en Green las
pruebas existentes del almacenamiento privado. CA-RF03-02 a CA-RF03-06 siguen
sin implementar. CA-RF03-01 queda implementado y comprobado localmente, con
evidencia y commit pendientes.
