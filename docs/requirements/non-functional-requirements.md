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

#### Verificación

- El requisito y criterio están aprobados antes de crear la prueba.
- La bitácora identifica comando, prueba y causa exacta del Red.
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

#### Hitos reprogramados el 2026-08-25

| Fecha | Resultado exigido | Estado actual |
| --- | --- | --- |
| 25 de agosto | Checkpoint del catálogo aprobado y puerta base recuperada | Completado |
| 26–28 de agosto | RF-01 implementado y verificado por incrementos | Pendiente |
| 29–31 de agosto | RF-02 implementado y verificado por incrementos | Pendiente |
| 1–3 de septiembre | RF-03 implementado y verificado por incrementos | Pendiente |
| 4–6 de septiembre | RF-12 implementado y verificado por incrementos | Pendiente |
| 7 de septiembre | Fixture de demostración, revisión de alcance y evidencias de catálogo | Pendiente |
| 8 de septiembre | Versión candidata, decisión explícita de alcance y congelación de funcionalidades | Pendiente |
| 9–11 de septiembre | Regresión, seguridad, permisos, integridad y rendimiento | Pendiente |
| 12 de septiembre | Reproducción limpia, documentación y evidencias académicas | Pendiente |
| 13 de septiembre | Portfolio, revisión del historial y ensayo de entrevista técnica | Pendiente |
| 14 de septiembre | Auditoría final y corrección exclusiva de defectos bloqueantes | Pendiente |
| 15 de septiembre | Entrega y etiqueta v1.0.0 si toda la puerta de calidad está verde | Pendiente |

#### Reglas de planificación

- Los requisitos `Must` y el recorrido backend tienen prioridad sobre los
  elementos `Should` y el acabado visual.
- Desde el 8 de septiembre no se añaden capacidades nuevas: se consolidan las
  implementadas y se puede recortar alcance no esencial.
- Un hito se mueve o recorta de forma explícita; no se declara completado con
  pruebas fallidas, permisos incompletos o archivos privados expuestos.
- El 15 de septiembre sigue siendo una fecha de verificación y entrega, no una
  jornada para desarrollar funcionalidades.

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
- El desarrollador escribe o comprende el criterio, confirma el Red, revisa la
  implementación y explica la migración.
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

## 5. Criterio de verificación de versión

Un RNF pasa a `Verificado` únicamente cuando su evidencia corresponde a una
versión o commit existente. Si una comprobación no puede ejecutarse, se registra
la limitación y el RNF conserva su estado anterior; no se sustituye el resultado
por una suposición.
