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

## Norma permanente de trazabilidad con GitHub Copilot

A partir de 2026-08-19, toda interacción con GitHub Copilot relacionada con
Foleyra se registrará en este documento, incluso cuando solo produzca análisis,
revisión o propuestas y no se modifique código. Las decisiones deben tomar
`.github/copilot-instructions.md` como marco general del proyecto y respetar
las fuentes de verdad que dicho documento establece.

Cada registro incluirá:

1. fecha y asistente utilizado;
2. el prompt completo, con secretos omitidos o redactados;
3. alcance autorizado y alcance excluido;
4. fuentes revisadas;
5. acciones realizadas y archivos modificados, o la indicación explícita de
   que no hubo modificaciones;
6. comprobaciones ejecutadas y sus resultados observados, separados de las
   pruebas solamente propuestas;
7. decisiones, riesgos, trabajo pendiente y commit asociado, o la indicación
   explícita de que no se creó un commit.

No se registrarán como realizadas acciones, pruebas, evidencias o decisiones
que no se hayan completado y comprobado.

## Registro — 2026-08-19 — Revisión estructural inicial con GitHub Copilot

- Herramienta: GitHub Copilot.
- Alcance autorizado: revisar exclusivamente el alcance del MVP, las
  aplicaciones Django necesarias, las responsabilidades modulares, la
  configuración de Django y PostgreSQL, el usuario personalizado previo a las
  migraciones y la separación entre `config`, `apps`, `docs` y `.github`.
- Fuera de alcance: implementar funcionalidades, cambiar código o configuración,
  crear migraciones, modificar dependencias, ejecutar pruebas o crear commits.

### Prompt utilizado

```text
Revisa unicamente la estructura del proyecto: - Alcance del MVP, Aplicaciones Django necesarias., Responsabilidad de cada módulo, Configuración de Django y PostgreSQL., Usuario personalizado antes de migrar, Separación entre config, apps, docs y .github.   No implementar nada. Añadir como norma a partir de ahora cualquier prompt y trazabilidad con este agente, al fichero ai-assisted-development.md ya que debo documentar siempre este proceso. Toma copilot-instructions.md como estructura general del proyecto en todas las tomas de decisiones. No implementes nada. No modifiques dependencias. Propon unicamente las pruebas necesarias.
```

### Fuentes consultadas en esta sesión

- `.github/copilot-instructions.md` y las instrucciones aplicables.
- `.python-version`, `requirements.in` y `requirements-dev.in`.
- `docs/technology-stack.md`, `docs/installation.md`,
  `docs/technical-log.md`, `docs/requirements/` y `docs/decisions/`.
- `config/settings.py`, `config/urls.py`, `compose.yaml` y la aplicación
  `apps.users`, incluida su migración inicial y sus pruebas.

### Acciones y resultado observado

- Se revisó el estado del repositorio y se preservaron los cambios locales
  existentes.
- Se añadió la norma permanente de trazabilidad en este documento.
- No se modificaron aplicaciones, configuración, migraciones, dependencias ni
  pruebas.
- No se ejecutaron pruebas; esta interacción solicitó una revisión estructural
  y únicamente la propuesta de pruebas necesarias.
- Los requisitos funcionales de dominio permanecen en estado `Propuesto`; no
  se autorizó crear aplicaciones de catálogo, carrito, pedidos, pagos o
  licencias.
- No se creó ningún commit.

## Registro — 2026-08-19 — Cierre de la revisión estructural

- Herramienta: GitHub Copilot.
- Alcance autorizado: presentar el cierre de la revisión con los seis puntos
  solicitados sobre estructura y arquitectura del proyecto.
- Fuera de alcance: nuevas comprobaciones, implementación, cambios de código o
  configuración, migraciones, dependencias, pruebas y commits.

### Prompt utilizado

```text
Termina con estos puntos
 - Revisar Alcance del MVP.
- Aplicaciones Django necesarias.
- Responsabilidad de cada módulo.
- Configuración de Django y PostgreSQL.
- Usuario personalizado antes de migrar.
- Separación entre config, apps, docs y .github.
```

### Acciones y resultado observado

- Se reutilizaron exclusivamente las fuentes y hallazgos documentados en el
  registro de revisión estructural inmediatamente anterior.
- Se añadió este registro de cierre; no hubo otros cambios.
- No se ejecutaron pruebas ni se creó ningún commit.

## Registro — 2026-08-19 — Actualización documental del checkpoint

- Herramienta: GitHub Copilot.
- Alcance autorizado: actualizar el README y la bitácora técnica con el estado
  comprobado del entorno Django.
- Fuera de alcance: código de dominio, configuración, migraciones,
  dependencias, requisitos funcionales y commits.

### Solicitud recibida

```text
Actualiza el README y la bitacora técnica.
```

### Contexto revisado

- `.github/copilot-instructions.md`, `.python-version`, `requirements.in` y
  `requirements-dev.in`.
- `docs/technology-stack.md`, `docs/installation.md`, `docs/technical-log.md`,
  los ADR y los requisitos funcionales.
- `tests/test_environment.py` y `apps/users/tests/test_user_model.py`.

### Resultado de la actualización

- Se creó el contenido de `README.md` con el estado actual del proyecto, los
  requisitos locales, las comprobaciones y enlaces documentales.
- Se añadió una entrada a `docs/technical-log.md` para distinguir esta
  actualización documental del cambio de pruebas de entorno ya registrado.
- No se expusieron valores de `.env` ni se presentó ningún requisito en estado
  `Propuesto` como implementado.
- `.venv/bin/python -m pytest tests/test_environment.py -q`: 2 pruebas
  superadas.
- `.venv/bin/python -m pytest -q`: 3 pruebas superadas.
- `git diff --check` y `git diff --cached --check`: sin errores.
- No se creó ningún commit.

## Registro — 2026-08-25 — Aprobación, recuperación y alineación del catálogo

- Herramienta: GitHub Copilot.
- Responsable de las decisiones: `acarras93-alt`, propietario del repositorio.
- Alcance autorizado: revisar el checkpoint del catálogo, recuperar PostgreSQL,
  ejecutar la puerta base y alinear la documentación con el estado observado.
- Fuera de alcance: implementar RF-01 a RF-15, modificar modelos o migraciones,
  añadir dependencias, crear evidencias funcionales o commits.

### Solicitudes recibidas

```text
He aprobado y documentado las decisiones pendientes del catalogo. Checkpint
habilitado para comenzar el ciclo test-firts. Comprueba el checkpoint tecnico
que acabo de realizar.

Haz estas indicaciones:
1. Inicia Docker Desktop, ejecuta docker compose up -d db, confirma estado
   healthy con docker compose ps y repite pytest.
2. Ejecuta las verificaciones con set -e o &&.
3. Actualiza la bitácora con el resultado real.

Soluciona y actualiza la documentacion con el estado actual del proyecto.
```

### Fuentes revisadas

- Instrucciones del repositorio, requisitos funcionales y no funcionales,
  checkpoint del catálogo, ADR, bitácora, flujos de Copilot e instalación.
- Estado Git, configuración Django, modelo y migración inicial de `apps.catalog`.
- Contenedor PostgreSQL y resultados reales de pytest y de la puerta de calidad.

### Acciones y resultados observados

- Se comprobó que el checkpoint aprobó D-CAT-02 a D-CAT-09 y habilita iniciar
  CA-RF01-01, sin declarar interfaces de catálogo implementadas.
- El primer pytest falló por PostgreSQL no disponible: `4 passed, 1 warning,
  3 errors`. Tras iniciar Docker Desktop, el contenedor quedó `healthy` y la
  repetición finalizó con `7 passed`.
- La puerta base se ejecutó con `set -e`; comprobaciones de Django, migraciones,
  pytest, Ruff, `pip check` y `git diff --check` terminaron correctamente. El
  único aviso fue el de permisos de caché de pip ya conocido.
- Se actualizaron README, flujos de trabajo, planning, checkpoint, bitácora y
  guía de entrevista para distinguir estructura existente, decisiones aprobadas
  e incrementos funcionales pendientes.
- No se modificaron modelos, migraciones, dependencias ni código de negocio
  durante esta sesión de alineación documental.
- Tras revisar `git diff` y `git diff --staged`, se creó el checkpoint
  `4b13fd4 feat: add catalog domain models` antes de iniciar RF-01.

### Riesgos y trabajo pendiente

- RNF-11 conserva el estado `Aprobado`; ningún requisito funcional pasa a
  `Implementado` o `Verificado` por estas comprobaciones de entorno.
- El siguiente incremento es CA-RF01-01: prueba Red válida para el selector
  compartido, implementación mínima, Green y evidencia posterior.


## Registro — 2026-09-26 — RF-09: acompañamiento test-first y cierre

- Herramienta: Codex.
- El desarrollador analizó los criterios, editó pruebas y componentes y ejecutó
  las comprobaciones durante el trabajo guiado. La asistencia explicó
  responsabilidades, propuso pruebas y cambios mínimos y revisó los resultados.
- El alcance de cierre solicitado fue actualizar la documentación y crear un
  commit que incluyera el trabajo de RF-09 y dejara el árbol limpio.
- Se revisaron requisitos, diff, vistas, plantillas y pruebas. En el cierre se
  completaron fecha y enlace al detalle del listado, previstos en el flujo,
  con una ampliación de prueba RED-GREEN. Se corrigieron dos erratas en nombres
  de pruebas para que la documentación use los identificadores definitivos.
- La puerta automatizada completa finalizó con `172 passed in 19.50s`, controles
  de Django y migraciones correctos, Ruff y formato correctos y dependencias sin
  conflictos. La evidencia está en `docs/evidence/RF-09/`.
- RF-09 queda `Implementado`; la documentación distingue las capturas y revisión
  visual pendientes y la futura extensión de CA-RF09-09 a modelos aún ausentes.
- Se conserva el historial de cambios del usuario. No se añadieron dependencias,
  no se modificaron migraciones y no se publicaron cambios en un remoto.


## Registro — 2026-09-27 — Especificación del cierre del MVP

- Herramienta: Codex, con revisión paralela de pagos/entrega y API/Admin.
- Encargo: comprobar el estado y redactar criterios restantes en el orden
  RF-07, RF-08, RF-10, RF-11, RF-13, RF-14 y RF-15; formalizar seis preguntas o
  precondiciones/recorrido cuando ya exista comportamiento.
- Fuentes: requisitos/RNF, código y pruebas locales, estado Git y captura de
  comprobaciones aportada por el desarrollador. La información de los documentos
  se contrasta con el encargo; no se ejecutan fases futuras por estar descritas.
- Resultado: contratos propuestos, dependencias explícitas, recorridos y plan
  por hitos sin mantener el 1 de octubre. Se preservan siete CA aprobados de
  RF-15; nuevas decisiones y cinco CA adicionales permanecen propuestos.
- Se alinean requisitos, README, flujos y prompts de pruebas con el Green
  inicial de comportamiento existente. El desarrollador mantiene la revisión
  de cada criterio y la comprensión de sus pruebas y componentes.
- Verificación propia: Ruff y formato correctos (114 archivos), Git inicial
  limpio y revisión del diff/documentación. Las 172 pruebas corresponden a la
  captura del usuario; no se presentan como nueva ejecución de Codex.
- No se implementan funcionalidades, migraciones ni dependencias; tampoco se
  ejecutan commits o publicación remota en esta revisión.

## Registro — 2026-10-11 — Revisión y publicación del estado de desarrollo

- Herramienta: Codex, sin delegación a subagentes.
- Encargo del desarrollador: «Haz un git push con el estado actual de Foleyra,
  actualiza la documentación antes de hacerlo».
- Fuentes: diff y estado Git, código, pruebas, migraciones, requisitos,
  instrucciones del repositorio y documentación existente.
- Trabajo: conservar el incremento parcial de RF-10, actualizar estado y
  pendientes, completar instrucciones de instalación y registrar evidencia real.
  Se ordena un import señalado por Ruff y se limpia un espacio de una plantilla.
- Control humano: el desarrollador inicia Docker Desktop cuando la sesión no
  consigue arrancarlo. Las pruebas se ejecutan después con PostgreSQL saludable.
- Resultados: 30 pruebas seleccionadas y 250 en batería completa satisfactorias;
  Django, migraciones, Ruff, formato y dependencias correctos. La prueba vacía
  con `pass` se identifica y no se atribuye a ella una garantía demostrada.
- Evidencia: `docs/evidence/RF-10/README.md` y su puerta del 2026-10-11.
- Límites: sin implementación de nuevos criterios, migraciones en la base local,
  cambio de dependencias, cierre formal de RF-10 ni despliegue. La solicitud
  autoriza versionar y publicar los cambios actuales; no autoriza reducir el
  alcance del MVP ni considerar realizadas evidencias pendientes.
