# Flujo de desarrollo del catálogo v0.2.0

## Objetivo

Separar con claridad cuatro actividades que no deben confundirse:

1. aprendizaje e instalación manual siguiendo la documentación de Django;
2. asistencia y revisión con GitHub Copilot;
3. pruebas y verificaciones reproducibles;
4. actualización documental y evidencias reales.

El objetivo de v0.2.0 es una sección vertical completa: catálogo web, detalle y
preview, búsqueda y filtros, y API pública. El diseño visual es secundario frente
al modelo, las consultas, los permisos y la protección de archivos.

## Puerta de entrada

El [checkpoint de decisiones](requirements/catalog-decision-checkpoint.md) quedó
aprobado el 2026-08-25. `apps.catalog`, el modelo base y
`catalog.0001_initial` ya existen; la siguiente conducta autorizada es
CA-RF01-01. La secuencia obligatoria para cada conducta nueva es:

```text
Requisito aprobado
  → decisiones aplicables aprobadas
  → prueba Red
  → implementación Green
  → verificación
  → evidencia
  → requisito verificado
```

Cambiar el estado documental no sustituye las pruebas. Del mismo modo, tener
código que funciona no autoriza a declarar un requisito verificado sin su
trazabilidad.

## Reparto de responsabilidades

| Actividad | Trabajo manual del desarrollador | Uso de Copilot | Resultado verificable |
|---|---|---|---|
| Decidir | Explicar y aprobar modelo, precio, preview, rutas y Admin | Detectar contradicciones y alternativas | Checkpoint firmado y RF aprobados |
| Aprender | Leer la sección oficial aplicable de Django o DRF | Resumir dudas concretas, no sustituir la lectura | Notas y decisión comprendida |
| Preparar app | Ejecutar los comandos, revisar estructura y registrar la app | Revisar nombres, imports y límites del módulo | `manage.py check` correcto |
| Diseñar prueba | Definir el comportamiento observable y sus datos | Proponer el caso mínimo con `/write-tests` | Fallo Red por ausencia del comportamiento |
| Implementar | Leer y aceptar cada línea del cambio mínimo | Proponer con `/implement-requirement` | Prueba objetivo Green |
| Revisar | Inspeccionar migración, diff, permisos y datos privados | Segunda revisión con `/review-change` | Hallazgos resueltos o riesgos registrados |
| Verificar | Ejecutar comandos en el entorno real | Ayudar a interpretar fallos reproducibles | Suite y controles con resultado real |
| Documentar | Actualizar estado, trazabilidad y explicación personal | Comprobar coherencia y omisiones | Log, RF y evidencia alineados |
| Versionar | Seleccionar archivos y crear un commit pequeño | Proponer mensaje, nunca confirmar por cuenta propia | Commit estable y árbol revisado |

## Paquetes de trabajo

### WP-00 — Aprobar el contrato

**Estado:** completado el 2026-08-25 por `acarras93-alt`, propietario del
repositorio.

Trabajo manual:

1. revisar D-CAT-01 a D-CAT-09;
2. elegir la vía de carga de datos de v0.2.0;
3. confirmar destinos de licencia, formatos y política de preview;
4. cambiar a `Aprobado` solo los RF cuyo contrato esté cerrado;
5. registrar fecha y responsable de la aprobación.

Copilot:

```text
/plan-requirement requirementId=RF-01
```

Resultado observado: checkpoint aprobado, RF-01, RF-02, RF-03, RF-12 y RF-15
en estado `Aprobado`, y CA-RF01-01 seleccionado como siguiente incremento.

### WP-01 — Preparar `apps.catalog`

**Estado:** completado el 2026-08-21.

La aplicación ya está creada y registrada como
`apps.catalog.apps.CatalogConfig`. No se debe volver a ejecutar `startapp` ni
crear una segunda estructura de catálogo.

Resultado observado:

1. `CatalogConfig.name` usa `apps.catalog`.
2. La aplicación está incluida en `INSTALLED_APPS`.
3. La configuración conserva PostgreSQL como única base de datos.
4. No existen modelos de carrito, pedido, pago, licencia ni descarga.

La creación de la app es infraestructura del requisito, no evidencia de que
RF-01 esté implementado.

### WP-02 — Modelo de catálogo y migración

**Estado:** estructura base completada el 2026-08-21; comportamiento de catálogo
pendiente.

La migración inicial aplicada crea `Category`, `Product`, `LicenseType` y
`ProductLicenseOffer`, incluidas sus restricciones de unicidad, precio y
relaciones protegidas. La prueba de modelo actual verifica la separación entre
producto, licencia y oferta, pero no implementa RF-01.

Las decisiones aprobadas el 2026-08-25 que requieran campos, validaciones o
almacenamiento adicional se tratarán como incrementos test-first separados y,
si modifican el esquema, exigirán una migración generada y revisada. En
particular, no se declararán cubiertas las políticas de valores técnicos,
preview ni almacenamiento privado sin sus pruebas y configuración reales.

Para un ajuste futuro del modelo:

1. restricciones de `Category`;
2. características y estado de `Product`;
3. `LicenseType` por destino de uso;
4. unicidad y precio de `ProductLicenseOffer`;
5. relaciones protegidas y validaciones acordadas.

Para cada grupo:

```text
/write-tests requirementId=RF-01 criterion=CA-RF01-01
```

Ejecutar la prueba específica y conservar en la bitácora la causa exacta del
Red. En una conversación posterior:

```text
/implement-requirement requirementId=RF-01 criterion=CA-RF01-01
```

Si el ajuste exige persistencia:

```bash
.venv/bin/python manage.py makemigrations catalog
.venv/bin/python manage.py migrate --plan
```

Antes de aplicar la migración, comprobar manualmente:

- nombres de tablas y dependencias;
- tipos y precisión de precio;
- restricciones únicas y `CheckConstraint`;
- comportamiento `PROTECT` esperado;
- ausencia de modelos o campos fuera de alcance.

Aplicar `migrate` únicamente cuando la migración revisada corresponda al diseño
aprobado.

### WP-03 — RF-01: consulta y listado público

Dividir RF-01 por criterios, sin implementar RF-02 o RF-03 accidentalmente:

1. selector de productos disponibles;
2. carga eficiente de categoría y precio mínimo;
3. vista pública y URL `/catalog/`;
4. template de lista y estado vacío;
5. paginación de 12 y 404 para página inválida;
6. prueba negativa de archivo maestro.

La prueba de N+1 debe medir consultas con uno y con varios productos. No debe
limitarse a comprobar que aparece una llamada a `select_related()` en el código.

Comprobación manual:

- visitante anónimo;
- producto disponible e inactivo;
- catálogo vacío;
- primera y segunda página;
- código fuente HTML sin ruta o URL del maestro.

Al finalizar WP-03 se puede marcar RF-01 como `Implementado`. Solo pasa a
`Verificado` después de la suite, la revisión manual y las evidencias reales.

### WP-04 — RF-02: detalle y preview

Implementar después de RF-01:

1. selector de detalle por `slug` sobre el mismo conjunto disponible;
2. metadatos técnicos y ofertas activas;
3. preview pública separada;
4. 404 para producto no disponible;
5. ausencia o fallo de preview sin fallback al maestro.

La evidencia debe usar audio y datos propios o ficticios, no activos descargados
del sitio de referencia.

### WP-05 — RF-03: búsqueda, filtros y orden

Antes de iniciar un criterio, comprobar el
[checkpoint específico de RF-03](requirements/rf03-decision-checkpoint.md) y
cerrar sus conflictos técnicos previos sin implementar parámetros de consulta.

Implementar un parámetro cada vez. Orden sugerido:

1. `q`;
2. `category` y `license`;
3. lista cerrada de `ordering`;
4. conservación de parámetros al paginar;
5. estado vacío y controles conservados;
6. errores 400 acordados y evidencia del 404 preexistente.

Los filtros por formato, frecuencia de muestreo y profundidad de bits quedan
fuera de v0.2.0. CA-RF03-07 reutiliza el 404 ya probado por RF-01 y se registra
como Green preexistente; no se revierte código correcto para forzar un Red.

No se añade `django-filter` en v0.2.0 porque no es una dependencia aprobada. Si
la implementación manual deja de ser razonable, se propone el cambio de
dependencias por separado y se vuelve a bloquear con pip-tools.

### WP-06 — RF-12: API pública

La API se implementa al final del catálogo para reutilizar comportamiento ya
probado:

1. serializers con lista explícita de campos públicos;
2. vistas DRF de solo lectura;
3. `AllowAny` declarado explícitamente;
4. paginación por página de 12;
5. mismos filtros y productos que la web;
6. pruebas de métodos 405 y ausencia del maestro.

La prueba de equivalencia debe comparar identificadores o `slug` de resultados,
no HTML y JSON completos.

### WP-07 — Administración del catálogo en v0.9.0

Registrar únicamente `Category`, `Product`, `LicenseType` y
`ProductLicenseOffer`. Configurar columnas, búsqueda, filtros y
`list_select_related` que aporten valor real.

Verificar por separado:

- usuario no `staff`;
- `staff` sin permiso de cambio;
- administrador de catálogo autorizado;
- desactivación reflejada en web y API;
- ausencia de rutas privadas en listados.

D-CAT-08 aprobó una fixture ficticia para v0.2.0, por lo que este paquete queda
aplazado a v0.9.0. La fixture es únicamente dato de demostración y no
implementa RF-15.

## Verificaciones de cierre de cada paquete

Ejecutar primero la prueba objetivo y después:

```bash
set -e
.venv/bin/python manage.py check --database default
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py migrate --check
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pip check
git diff --check
git status --short
```

Para RF-01, RF-02 y RF-12 añadir pruebas explícitas de consultas y privacidad.
No registrar como superada una comprobación que no se haya ejecutado.

## Actualización documental después de Green

En el mismo paquete lógico:

1. actualizar la trazabilidad del RF con rutas reales de pruebas y código;
2. añadir una entrada a `docs/technical-log.md` con Red, Green y verificaciones;
3. actualizar README solo si cambia el uso visible del proyecto;
4. actualizar `docs/installation.md` solo si cambia la reproducción desde cero;
5. guardar evidencias reales en `docs/evidence/RF-XX/`;
6. registrar la interacción correspondiente en
   `docs/ai-assisted-development.md` cuando se utilice GitHub Copilot;
7. revisar `git diff` y seleccionar archivos explícitamente.

Estados:

- `Aprobado`: contrato cerrado, todavía sin código.
- `Implementado`: comportamiento construido y pruebas objetivo Green.
- `Verificado`: suite, controles, comprobación manual y evidencia completados.

## Secuencia de commits propuesta

Todos deben dejar el repositorio en verde:

1. `docs: define catalog requirements and decisions`
2. `feat: add catalog domain models`
3. `feat: implement public catalog listing`
4. `feat: add product detail and public preview`
5. `feat: add catalog search and filters`
6. `feat: expose public catalog API`
7. `feat: configure catalog administration` — solo si D-CAT-08 lo aprueba
8. `docs: record catalog verification evidence`

El checkpoint de base del modelo y sus decisiones se registra antes de iniciar
RF-01. Los commits posteriores se crearán únicamente al completar y verificar
el incremento correspondiente.

## Calendario reprogramado hasta la entrega

| Fecha | Resultado esperado | Estado al 2026-08-25 |
| --- | --- | --- |
| 25 de agosto | Checkpoint aprobado, entorno recuperado y puerta base ejecutada | Completado |
| 26–28 de agosto | RF-01 por incrementos test-first y evidencias reales | Pendiente |
| 29–31 de agosto | RF-02 por incrementos test-first y evidencias reales | Pendiente |
| 1–3 de septiembre | RF-03 por incrementos test-first y evidencias reales | Pendiente |
| 4–6 de septiembre | RF-12 por incrementos test-first y evidencias reales | Pendiente |
| 7 de septiembre | Fixture de demostración, revisión de alcance y evidencias de catálogo | Pendiente |
| 8 de septiembre | Versión candidata y congelación de funcionalidades | Pendiente |
| 9–11 de septiembre | Consolidación: regresión, seguridad, permisos e integridad | Pendiente |
| 12 de septiembre | Instalación limpia, documentación y evidencias académicas | Pendiente |
| 13 de septiembre | Portfolio, historial Git y ensayo de defensa | Pendiente |
| 14 de septiembre | Auditoría final y corrección exclusiva de defectos bloqueantes | Pendiente |
| 15 de septiembre | Verificar y entregar v1.0.0; no desarrollar funcionalidades | Pendiente |

El calendario se replanifica recortando alcance `Should`, nunca ocultando
pruebas fallidas, permisos incompletos o exposición de archivos privados.
