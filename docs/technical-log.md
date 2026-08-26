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
