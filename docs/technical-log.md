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
