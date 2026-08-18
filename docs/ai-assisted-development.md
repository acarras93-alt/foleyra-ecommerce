# Registro de desarrollo asistido por IA

## Propósito

Este documento aporta trazabilidad sobre el uso de asistentes de IA. La IA se
utiliza como herramienta de apoyo; la responsabilidad sobre las decisiones, la
revisión, las pruebas y la aceptación de cada cambio sigue siendo humana.

## Fase 01 — Inicialización de Django

- Fecha: 2026-08-18.
- Herramienta: ChatGPT Codex.
- Alcance autorizado: crear el esqueleto Django, configurar PostgreSQL, definir
  el usuario personalizado antes de la primera migración, verificar y crear
  commits pequeños.
- Fuera de alcance: funcionalidades del catálogo y dependencias nuevas.

### Prompt utilizado

El siguiente prompt se conserva literalmente como evidencia del encargo:

```text
Actúa como desarrollador senior especializado en Django, Django REST Framework y PostgreSQL.

Estado actual:

- Python 3.12.13.
- Django 5.2.17.
- PostgreSQL 18.6 mediante Docker Compose.
- Dependencias bloqueadas con pip-tools.
- Variables privadas en `.env`.
- Repositorio e infraestructura verificados.
- No se ha creado todavía el proyecto Django.

Fuentes de verdad:

- requirements.in
- requirements-dev.in
- docs/technology-stack.md
- docs/installation.md
- docs/decisions/
- docs/requirements/
- docs/technical-log.md

Objetivo de esta fase:

Crear manualmente la estructura Django, configurar PostgreSQL y definir un usuario personalizado antes de la primera migración.

Restricciones:

- No utilizar SQLite.
- No ejecutar migrate antes de configurar AUTH_USER_MODEL.
- No añadir dependencias sin aprobación.
- Avanzar mediante verificaciones y commits pequeños.
- No implementar todavía funcionalidades del catálogo.
```

### Acciones implementadas

1. Se creó manualmente la estructura del proyecto `config`.
2. Se creó la aplicación `apps.users`.
3. Se configuró PostgreSQL mediante variables cargadas desde `.env`.
4. Se definió `AUTH_USER_MODEL = "users.User"` antes de migrar.
5. Se generó la migración inicial de `users.User`.
6. Se revisó el plan y se aplicó la primera migración sobre PostgreSQL.
7. Se añadieron pruebas de configuración y persistencia.
8. Se verificaron Django, migraciones, pytest, Ruff y dependencias.
9. Se actualizó la documentación técnica y de instalación.

### Verificación final registrada

- PostgreSQL 18.6 estaba saludable.
- Django utilizó el backend `django.db.backends.postgresql`.
- El modelo activo fue `users.User`.
- Se creó la tabla `users_user`.
- No se creó la tabla sustituida `auth_user`.
- No quedaron migraciones pendientes.
- Las tres pruebas existentes finalizaron correctamente.
- Ruff y `pip check` finalizaron sin errores.
- No se incorporó SQLite, ninguna dependencia nueva ni código de catálogo.

### Commits creados

- `84a5c69 feat: initialize Django with custom user`
- `32aa2b1 feat: add initial custom user migration`
- `049a6bc test: verify custom user persistence`
- `55673aa docs: record Django initialization checkpoint`

## Política a partir de la fase siguiente

El desarrollo posterior se realizará con GitHub Copilot como asistente
principal. Antes de aceptar un cambio será obligatorio:

1. partir de un requisito y criterios de aceptación aprobados;
2. leer y comprender el diff completo;
3. poder explicar la decisión y el código sin depender del asistente;
4. comprobar primero el fallo esperado de las pruebas nuevas;
5. ejecutar las verificaciones aplicables después de implementar;
6. rechazar cambios ajenos al alcance o dependencias no autorizadas;
7. crear commits pequeños que dejen el repositorio en estado válido;
8. registrar las decisiones y evidencias reales.

El cambio de herramienta no altera la autoría ni la responsabilidad: las
sugerencias de Copilot solo se incorporan cuando han sido revisadas y
aceptadas conscientemente.
