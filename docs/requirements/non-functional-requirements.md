# Requisitos no funcionales de Foleyra

## 1. Propósito

Este documento define las condiciones de calidad, seguridad y proceso que debe
cumplir el MVP. Los RNF se verifican sobre comportamiento y evidencias reales;
no se consideran satisfechos por la mera presencia de una configuración, una
llamada ORM o una prueba escrita que no se haya ejecutado.

Los estados posibles son:

- `Propuesto`: la condición está definida, pero todavía requiere aprobación.
- `Aprobado`: forma parte obligatoria del alcance de calidad.
- `Verificado`: existe evidencia reproducible para la versión indicada.

La aprobación de un RNF no significa que todas las versiones futuras ya lo
cumplan. Cada entrega debe volver a verificar los RNF que le resulten aplicables.

## 2. Índice

| ID | Título | Aplicación principal | Estado |
|---|---|---|---|
| RNF-01 | Gestión segura de secretos | Todo el sistema | Aprobado |
| RNF-02 | Entorno reproducible sobre PostgreSQL | Instalación y entrega | Aprobado |
| RNF-03 | Desarrollo guiado por pruebas | Reglas y comportamiento | Aprobado |
| RNF-04 | Trazabilidad verificable | Requisitos y evidencias | Aprobado |
| RNF-05 | Coherencia entre web y API | Interfaces públicas y privadas | Aprobado |
| RNF-06 | Separación entre audio público y privado | Catálogo y descarga | Aprobado |
| RNF-07 | Eficiencia de consultas del catálogo | Web, API y Admin | Aprobado |
| RNF-08 | Integridad de datos en PostgreSQL | Dominio y pedidos | Aprobado |
| RNF-09 | Consultas públicas deterministas y seguras | Catálogo web y API | Aprobado |
| RNF-10 | Mínimo privilegio y control de acceso | Admin y funciones privadas | Aprobado |
| RNF-11 | Puerta de calidad de cada incremento | Desarrollo y release | Aprobado |
| RNF-12 | Planificación por hitos y congelación funcional | Release v1.0.0 | Aprobado |
| RNF-13 | Control humano del desarrollo asistido por IA | Proceso de desarrollo | Aprobado |

## 3. Especificación detallada

### RNF-01 — Gestión segura de secretos

#### Requisito

Los secretos y credenciales se obtienen del entorno y no se almacenan en Git,
código, fixtures, pruebas, documentación, prompts o evidencias.

#### Verificación

- `.env` está ignorado y `git ls-files .env` no produce salida.
- `.env.example` contiene únicamente nombres y marcadores no operativos.
- Configuración, errores, capturas y diffs no contienen claves, contraseñas,
  tokens ni credenciales reales.
- El código no proporciona valores por defecto inseguros para secretos
  obligatorios.

#### Evidencia

- Revisión de `.gitignore`, `.env.example`, archivos rastreados y diff.
- Instalación correcta usando un `.env` local no versionado.

### RNF-02 — Entorno reproducible sobre PostgreSQL

#### Requisito

El proyecto se puede instalar desde cero con Python 3.12.13, dependencias
bloqueadas y PostgreSQL 18.6 mediante Docker Compose. SQLite no se utiliza como
alternativa de desarrollo ni de pruebas.

#### Verificación

- `pip-sync` reproduce los ficheros de bloqueo y `pip check` no detecta
  incompatibilidades.
- `connection.vendor` es `postgresql` en las pruebas de arquitectura.
- `manage.py check --database default` no detecta incidencias.
- `makemigrations --check --dry-run` y `migrate --check` no encuentran cambios
  o migraciones pendientes.
- Una reproducción limpia sigue únicamente README y `docs/installation.md`.

#### Evidencia

- Versiones observadas, comandos de instalación y resultado de los controles.
- Evidencia de la reproducción limpia previa a la versión candidata y a v1.0.0.

### RNF-03 — Desarrollo guiado por pruebas

#### Requisito

Cada comportamiento nuevo comienza con una prueba que falla por la ausencia de
ese comportamiento. El Red debe ser válido antes de escribir la implementación
mínima que obtiene Green.

Si el comportamiento completo ya existe, se escribe o amplía una prueba de
regresión y se ejecuta; puede comenzar en Green. Se registra como cobertura de
comportamiento preexistente, sin fabricar Red ni cambiar código que ya cumple.
Si ya existe una prueba suficiente, se reutiliza su trazabilidad y se ejecuta.

#### Verificación

- El requisito y criterio están aprobados antes de crear la prueba.
- La bitácora identifica comando, prueba y causa exacta del Red o, cuando ya
  existía el comportamiento, el Green inicial y el código que lo satisface.
- Un fallo de sintaxis, import, entorno o PostgreSQL no cuenta como Red válido.
- Después del Green se ejecutan la prueba específica y la regresión aplicable.
- No se debilitan, borran o marcan pruebas para ocultar un defecto.

#### Evidencia

- Entrada de bitácora y commit estable que contiene prueba e implementación.
- Salida real de la prueba objetivo y de la suite.

### RNF-04 — Trazabilidad verificable

#### Requisito

Cada incremento mantiene la cadena:

```text
Requisito → Decisión → Prueba → Implementación → Evidencia → Commit
```

#### Verificación

- Los estados `Propuesto`, `Aprobado`, `Implementado` y `Verificado` se usan de
  acuerdo con resultados reales.
- La tabla de trazabilidad enlaza rutas y referencias existentes.
- Las evidencias previstas no se presentan como realizadas.
- El commit indicado contiene únicamente un cambio coherente y deja el
  repositorio en estado válido.

#### Evidencia

- Requisito actualizado, bitácora, evidencia y referencia del commit.

### RNF-05 — Coherencia entre web y API

#### Requisito

Web y API son capas de presentación distintas sobre las mismas reglas de
negocio, selectores y servicios. Una interfaz no puede publicar, autorizar o
modificar un objeto que la otra considere no disponible ante condiciones
equivalentes.

#### Verificación

- RF-01, RF-02, RF-03 y RF-12 reutilizan los mismos selectores del catálogo.
- Las pruebas comparan los `slug` o identificadores devueltos por web y API ante
  los mismos datos y filtros.
- Serializers y templates transforman datos, pero no duplican reglas de
  disponibilidad.
- Las transiciones futuras de carrito, pedido, pago y licencia usan servicios
  compartidos.

#### Evidencia

- Pruebas de equivalencia y revisión de dependencias entre módulos.

### RNF-06 — Separación entre audio público y privado

#### Requisito

La preview promocional y el archivo maestro adquirido se almacenan y entregan
mediante políticas diferentes. El maestro no puede quedar accesible mediante
`MEDIA_URL`, un template, un serializer o una ruta predecible.

#### Verificación

- Las previews y los maestros usan raíces o backends de almacenamiento
  separados.
- Solo el almacenamiento de previews dispone de una ruta pública durante el
  desarrollo.
- HTML, contexto, JSON, errores, Admin público y logs no contienen nombre, ruta
  interna o URL del maestro.
- La ausencia o fallo de preview nunca provoca un fallback al maestro.
- RF-11 entrega el archivo únicamente después de comprobar usuario, pedido,
  licencia y autorización.

#### Evidencia

- Pruebas negativas en RF-01, RF-02 y RF-12.
- Inspección de rutas y configuración de almacenamiento.
- Pruebas de autorización de RF-11 cuando se implemente.

### RNF-07 — Eficiencia de consultas del catálogo

#### Requisito

Listar o serializar productos no provoca una consulta adicional por cada
categoría, licencia u oferta. La eficiencia se demuestra midiendo consultas,
no buscando llamadas concretas a `select_related()` o `prefetch_related()`.

#### Verificación

- Acceder a categoría y precio mínimo en RF-01 mantiene un número acotado de
  consultas al pasar de un producto a una página completa de 12.
- RF-02 carga ofertas activas en un número acotado de consultas.
- RF-12 no introduce N+1 durante la serialización.
- RF-15 usa carga relacionada en listados administrativos cuando muestra datos
  de relaciones.
- Las pruebas emplean recuento de consultas y evalúan los campos relacionados.

#### Evidencia

- Pruebas con uno y varios productos y resultado del recuento.
- Consulta o plan revisado cuando una optimización requiera explicación.

### RNF-08 — Integridad de datos en PostgreSQL

#### Requisito

Las invariantes que puedan expresarse de forma persistente se protegen mediante
tipos, claves, restricciones y relaciones de PostgreSQL, además de la validación
de entrada.

#### Verificación para el catálogo

- SKU y `slug` de producto son únicos.
- Los `slug` de categoría y licencia son únicos.
- Solo existe una oferta por combinación producto-licencia.
- El precio usa `DecimalField`, no `float`, y no admite valores negativos.
- Duración, frecuencia de muestreo y profundidad de bits son positivas.
- Las relaciones con valor histórico usan `PROTECT` o una política equivalente
  aprobada.
- No existe campo, validación ni operación de stock físico.

#### Verificación futura

- Las líneas de pedido guardan una instantánea de SKU, producto, licencia,
  versión de términos, precio y moneda.
- La modificación del catálogo no altera pedidos anteriores.
- Las transiciones críticas e idempotentes usan transacciones cuando el
  requisito lo exija.

#### Evidencia

- Migración generada y revisada, pruebas de modelo y restricciones observadas
  sobre PostgreSQL.

### RNF-09 — Consultas públicas deterministas y seguras

#### Requisito

La búsqueda, los filtros, la ordenación y la paginación aceptan únicamente un
contrato público limitado y producen resultados estables.

#### Verificación

- La página contiene 12 elementos y el consumidor no modifica su tamaño.
- Cada orden permitido añade un desempate único y estable.
- Los nombres de ordenación proceden de una lista cerrada; los valores del
  usuario no se convierten directamente en expresiones ORM.
- Un parámetro conocido inválido produce 400, una página inválida o inexistente
  produce 404 y una consulta válida sin resultados produce un estado vacío.
- Los enlaces web conservan búsqueda, filtros y orden al cambiar de página.
- La API devuelve una representación de error sin detalles internos.

#### Evidencia

- Pruebas de entradas válidas, inválidas, límites y paginación repetible.

### RNF-10 — Mínimo privilegio y control de acceso

#### Requisito

Cada interfaz declara permisos acordes a su finalidad. El catálogo y la preview
son públicos; Admin, carrito, pedidos, pagos, licencias y descargas requieren la
identidad y autorización correspondientes.

#### Verificación

- RF-12 declara `AllowAny` de manera explícita y solo permite lectura.
- Los métodos de escritura de la API pública responden 405.
- `is_staff` permite entrar en Admin, pero cada acción depende además de los
  permisos de modelo.
- Se prueban usuario anónimo, autenticado no `staff`, `staff` sin permiso y
  administrador autorizado.
- Un usuario no puede consultar o modificar recursos pertenecientes a otro.
- El Admin no evita servicios o invariantes en pagos, licencias o descargas.

#### Evidencia

- Matriz de permisos aprobada y pruebas positivas y negativas por rol.

### RNF-11 — Puerta de calidad de cada incremento

#### Requisito

Un incremento no se considera terminado hasta superar una puerta de calidad
proporcional al riesgo. Green en una única prueba no basta para declararlo
verificado.

#### Verificación mínima

```bash
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

Además:

- se revisan diff, archivos nuevos, migraciones, permisos y exposición de datos;
- se ejecuta la comprobación manual del recorrido afectado;
- se actualizan documentación y evidencias con resultados reales;
- no quedan defectos bloqueantes conocidos ni cambios ajenos al alcance.

#### Evidencia

- Entrada de bitácora con comandos y resultados observados.
- Árbol Git revisado y commit estable cuando el incremento se versiona.

### RNF-12 — Planificación por hitos y congelación funcional

#### Requisito

El planning se gestiona por resultados verificables y reserva una fase de
consolidación. Retrasar la versión final no autoriza a ampliar el MVP.

#### Hitos de referencia y foco actualizado el 2026-10-04

El calendario de agosto/septiembre queda sustituido. Por decisión del
desarrollador, el 1 de octubre tampoco es una fecha de entrega comprometida.
No se establece otra fecha sin estimar el trabajo pendiente con datos de avance.

| Orden | Resultado exigido |
|---|---|
| 1 · RF-07 | Pago simulado aprobado, íntegro e idempotente |
| 2 · RF-08 | Rechazo y reintento con historial y estados coherentes |
| 3 · RF-10 | Registro atómico y consulta privada de permisos con condiciones trazables |
| 4 · RF-11 | Entrega privada del archivo correcto para la compra |
| 5 · RF-13 | Carrito por API autenticada con reglas compartidas |
| 6 · RF-14 | Compra, consultas y entrega por API privada |
| 7 · RF-15 | Administración con permisos y protección de historia |
| 8 · Consolidación | Regresión, recorrido manual, evidencias e instalación limpia |

Los contratos y decisiones técnicas nuevos permanecen propuestos en los RF
hasta su aprobación; este orden y la metodología proceden del encargo actual.
El detalle está en el [plan del MVP](mvp-implementation-plan.md).

El foco inmediato acordado el 2026-10-04 es completar RF-10 y RF-11 y validar
después el recorrido web de adquisición y entrega. RF-07 y RF-08 ya constan
como verificados. RF-13, RF-14 y RF-15 conservan su alcance y estado: concentrar
el trabajo actual no los elimina ni permite declarar terminado todo el MVP.
El objetivo de una o dos semanas orienta la priorización; no certifica una fecha
de entrega ni autoriza a omitir garantías de seguridad o integridad.

#### Reglas de planificación

- Los requisitos `Must` y el recorrido backend tienen prioridad sobre nuevo
  acabado visual o ampliaciones ajenas al MVP.
- La congelación funcional comienza al cerrar el alcance acordado y antes de
  consolidación; durante ella se corrigen defectos y se prepara la entrega.
- Cada hito termina con criterios comprobados, documentación y puerta de
  calidad aplicable, no por llegar a una fecha.
- Un hito se reestima explícitamente; no se ocultan fallos, permisos incompletos
  o exposición de archivos para declarar una entrega.
- El ritmo debe permitir que el desarrollador comprenda y explique cada
  comportamiento; se trabaja por criterios, sin desarrollar todos a la vez.

#### Validación de extremo a extremo con productos sonoros reales

El cierre funcional del recorrido web incluye una validación con una muestra
reducida de audios reales, previews preparadas, cuentas de prueba y pagos
simulados. Se introduce un sonido durante RF-10/11 y se completa el recorrido
integrado después de su implementación; no se importa la biblioteca completa.

La verificación contrasta datos persistidos en PostgreSQL, archivos almacenados
y respuestas al usuario. Debe demostrar separación público/privado (RNF-06),
conservación histórica (RNF-08) y aislamiento entre propietarios (RNF-10).
Complementa las pruebas automatizadas y la puerta de calidad de RNF-11.

El protocolo, la muestra y las condiciones de cierre se describen en el
[plan del MVP](mvp-implementation-plan.md#validación-de-extremo-a-extremo-con-productos-sonoros-reales).
Las evidencias remiten a los criterios existentes de RF-10/11 e indican versión,
resultado y limitaciones, sin publicar secretos ni claves privadas del maestro.
La validación permanece pendiente hasta ejecutarla y registrar sus resultados.

#### Evidencia

- Planning actualizado, estado real de RF, lista de riesgos y resultado de la
  puerta de calidad de la versión candidata y final.

### RNF-13 — Control humano del desarrollo asistido por IA

#### Requisito

La asistencia de GitHub Copilot u otra herramienta acelera análisis, pruebas y
funciones acotadas, pero el desarrollador conserva la decisión, ejecución y
responsabilidad técnica.

#### Verificación

- El manual, los requisitos y las versiones bloqueadas se revisan antes del
  prompt.
- El desarrollador escribe o comprende el criterio, confirma un Red válido o
  un Green inicial justificado por comportamiento existente, revisa la
  implementación y explica la migración cuando exista.
- Aplica la [premisa de trabajo hasta el cierre del proyecto](mvp-implementation-plan.md#4-premisa-de-trabajo-hasta-el-cierre-del-proyecto),
  acordada el 2026-10-07: un criterio cada vez, lectura breve, revisión de
  cobertura existente, apoyo del asistente en la escritura de pruebas,
  aprendizaje centrado en la implementación y evidencia suficiente.
- El desarrollador revisa qué prepara la prueba, qué operación ejecuta y qué
  fallo detectan sus comprobaciones. El análisis se amplía solo ante una
  ambigüedad que cambia el comportamiento, un riesgo concreto o una parte del
  criterio sin cubrir. No se exige una investigación exhaustiva ni dominar
  toda la infraestructura de concurrencia antes de continuar; sus garantías
  siguen verificándose.
- La revisión con Copilot se realiza después en una conversación o fase
  separada y produce hallazgos reproducibles.
- No se acepta código que el desarrollador no pueda explicar ni verificar.
- Prompt, alcance, archivos y resultados se registran sin secretos.
- El notebook didáctico no prevalece sobre requisitos, ADR, pruebas o código
  cuando una edición antigua contiene decisiones superadas.

#### Evidencia

- `docs/ai-assisted-development.md`, bitácora técnica y revisión del diff.
- Manual versionado con el bloque aplicable actualizado antes de implementarlo.

## 4. Aplicación al catálogo v0.2.0

| Requisito funcional | RNF obligatorios |
|---|---|
| RF-01 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-08, RNF-09 y RNF-11 |
| RF-02 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-09 y RNF-11 |
| RF-03 | RNF-03, RNF-04, RNF-05, RNF-07, RNF-09 y RNF-11 |
| RF-12 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-09, RNF-10 y RNF-11 |
| RF-15 | RNF-01, RNF-03, RNF-04, RNF-06, RNF-07, RNF-08, RNF-10 y RNF-11 |

RNF-02, RNF-12 y RNF-13 se aplican transversalmente a todos los incrementos.

## 5. Aplicación a autenticación, carrito y pedido v0.3.0-v0.4.0

| Requisito funcional | RNF obligatorios |
|---|---|
| RF-04 | RNF-01, RNF-03, RNF-04, RNF-10 y RNF-11 |
| RF-05 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-06, RNF-08, RNF-10 y RNF-11 |
| RF-06 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-08, RNF-10 y RNF-11 |
| RF-09 | RNF-01, RNF-03, RNF-04, RNF-05, RNF-08, RNF-10 y RNF-11 |

Para RF-04, RNF-10 exige que las sesiones no otorguen privilegios y que las
funciones privadas requieran identidad. Para RF-05, RNF-05 obliga a concentrar
las transiciones del carrito en servicios reutilizables por RF-13, RNF-08
protege la pertenencia y la unicidad persistentes, y RNF-10 exige aislamiento
entre propietarios.

Para RF-06, RNF-08 exige instantáneas históricas y una transacción PostgreSQL
que no deje pedidos, líneas ni carritos parcialmente modificados. RNF-10 exige
que la conversión resuelva exclusivamente el carrito del cliente autenticado;
RNF-05 reserva la reutilización del servicio de pedido para la futura API de
RF-14.

Para RF-09, RNF-08 exige conservar la fecha de creación del pedido y consultar
la instantánea histórica sin depender del catálogo vivo. RNF-10 exige que el
listado y el detalle se limiten al propietario autenticado y traten los pedidos
ajenos como inexistentes. RNF-05 reserva una frontera reutilizable para la
futura API privada de RF-14 sin adelantarla.

RNF-02, RNF-12 y RNF-13 continúan aplicándose transversalmente a RF-04, RF-05,
RF-06 y RF-09.

## 6. Aplicación a los incrementos restantes del MVP

| RF | Comprobaciones de calidad a concretar al implementar su contrato |
|---|---|
| RF-07/08 | Propiedad, CSRF, importes históricos, unicidad de aprobación, idempotencia, rollback y concurrencia PostgreSQL |
| RF-10 | Un permiso por línea pagada, emisión atómica, condiciones históricas inmutables y consultables, versionado, documentación antigua explícita, aislamiento, consultas acotadas y GET sin efectos |
| RF-11 | Archivo privado correcto, referencia estable, ausencia de exposición, denegación uniforme y conservación del archivo comprado |
| RF-13/14 | Sesión y permisos explícitos, CSRF, contrato JSON, equivalencia web/API y consultas acotadas |
| RF-15 | Permisos por rol, historia protegida, formularios seguros de archivos y ausencia de N+1 |

Aplican RNF-01 a RNF-06, RNF-08 y RNF-10 a RNF-13 según la operación;
RNF-07 añade eficiencia del catálogo/Admin. Las reglas particulares nuevas se
especifican como propuestas en los RF, sin darlas por implementadas.
Los límites de consultas se prueban usando las relaciones, no por la mera
presencia de una optimización ORM. Las lecturas no deben crear ni modificar
datos de negocio para completar una transición omitida.

## 7. Criterio de verificación de versión

Un RNF pasa a `Verificado` únicamente cuando su evidencia corresponde a una
versión o commit existente. Si una comprobación no puede ejecutarse, se registra
la limitación y el RNF conserva su estado anterior; no se sustituye el resultado
por una suposición.
