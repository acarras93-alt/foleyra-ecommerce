# Requisitos funcionales de Foleyra

## 1. Propósito

Este documento define las capacidades funcionales del MVP de Foleyra y sus
ampliaciones posteriores, diferenciadas por alcance y estado. Constituye la fuente de verdad para la planificación,
las pruebas, la implementación y las evidencias académicas.

## 2. Convenciones

- Los requisitos utilizan identificadores estables `RF-XX`.
- Un requisito no se implementa sin criterios de aceptación aprobados.
- Los estados posibles son: Propuesto, Aprobado, Implementado y Verificado.
- Las evidencias reales se incorporan después de implementar el requisito.
- Web y API deben reutilizar las mismas reglas de negocio.

## 3. Índice de requisitos

> El índice reúne requisitos y evoluciones previstas. El cierre acordado con
> el instructor el 2026-10-21 requiere RF-11, RF-15 y validación del recorrido
> web. RF-13/14 y RF-16 quedan como evolutivos. Su presencia no implica
> implementación; el estado indica su grado real de desarrollo y verificación.

| ID | Título | Actor principal | Prioridad | Versión | Estado |
|---|---|---|---|---|---|
| RF-01 | Consultar el catálogo | Visitante o cliente | Must | v0.2.0 | Aprobado |
| RF-02 | Consultar el detalle y escuchar una preview pública | Visitante o cliente | Must | v0.2.0 | Aprobado |
| RF-03 | Buscar, filtrar, ordenar y paginar el catálogo | Visitante o cliente | Should | v0.2.0 | Verificado |
| RF-04 | Registrarse, iniciar sesión y cerrar sesión | Visitante o cliente | Must | v0.3.0 | Verificado |
| RF-05 | Gestionar los productos del carrito privado | Cliente autenticado | Must | v0.3.0 | Aprobado |
| RF-06 | Convertir el carrito en un pedido histórico | Cliente autenticado | Must | v0.4.0 | Implementado |
| RF-07 | Simular un pago aprobado de forma independiente | Cliente autenticado | Must | v0.5.0 | Verificado |
| RF-08 | Simular un pago fallido y reintentarlo | Cliente autenticado | Must | v0.5.0 | Verificado |
| RF-09 | Consultar los pedidos propios | Cliente autenticado | Must | v0.4.0 | Implementado |
| RF-10 | Registrar y consultar permisos de uso con condiciones trazables | Cliente autenticado | Must | v0.6.0 | Verificado |
| RF-11 | Descargar un archivo autorizado | Cliente autenticado | Must | v0.6.0 | Aprobado |
| RF-12 | Consultar el catálogo mediante una API pública | Consumidor de la API | Must | v0.2.0 | Verificado |
| RF-13 | Gestionar el carrito mediante una API autenticada | Cliente de la API autenticado | Must | v0.3.0 | Propuesto |
| RF-14 | Ejecutar checkout, pago y consultas privadas mediante API | Cliente de la API autenticado | Must | v0.7.0 | Propuesto |
| RF-15 | Administrar el sistema mediante Django Admin | Administrador | Must | v0.9.0 | Aprobado |

### Ampliaciones solicitadas el 2026-10-14

Estas propuestas amplían el alcance original. Sus criterios se redactan para
revisión e implementación por pasos; no se consideran implementados ni
verificados por incorporarlos a este documento. Los estados y evidencias de
RF-01 a RF-15 conservan su alcance anterior.

| ID | Título | Actor principal | Prioridad | Versión | Estado |
|---|---|---|---|---|---|
| RF-16 | Explorar el catálogo por familias y subfamilias sonoras | Visitante o cliente | Should | Evolución; por asignar | Propuesto |
| RF-17 | Completar el recorrido web mediante navegación visible | Visitante o cliente | Must | Evolución; por asignar | Propuesto |

La prioridad de RF-17 corresponde al bloqueo observado en el recorrido manual.
La numeración identifica requisitos; no determina el orden de implementación.
El [plan por etapas](mvp-implementation-plan.md#7-evolución-del-catálogo-y-recorrido-web-2026-10-14)
prioriza navegación, datos coherentes y evidencias antes de ampliar la jerarquía.

Las decisiones transversales que deben aprobarse antes de crear el módulo se
encuentran en el
[checkpoint de decisiones del catálogo](catalog-decision-checkpoint.md).

RF-07 queda verificado el 2026-10-02, RF-08 el 2026-10-03 y RF-10 el 2026-10-14.
La secuencia original incluía RF-13/14 antes de RF-15. La delimitación
confirmada con el instructor y registrada el 2026-10-21 fija el cierre en
**RF-11 → RF-15 → validación y entrega**; RF-13/14 y RF-16 permanecen como
evolutivos. El recorrido manual completo se realizará al finalizar la
integración web, conservando pruebas y regresiones por incremento. El
[plan de cierre y metodología](mvp-implementation-plan.md) registra el cierre
automatizado de RF-10
y la premisa de revisar cobertura existente y profundizar según dudas o riesgos.
De los seis requisitos antes vacíos, RF-11 queda aprobado el 2026-10-16;
RF-13/14 continúan como propuestas y los estados restantes se consultan en el
índice. RF-15 conserva CA01–CA07 aprobados y separa expresamente sus
ampliaciones propuestas.

## 4. Especificación detallada

### RF-01 — Consultar catálogo de productos activos

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Must |
| Versión objetivo | v0.2.0 |
| Estado | Aprobado |
| Dependencias | RNF-01, RNF-03 a RNF-09 y RNF-11 |

#### Objetivo

Permitir que cualquier visitante consulte los productos sonoros para los que
existe al menos una licencia disponible, sin necesidad de autenticarse.

#### Precondiciones

- La aplicación está disponible.
- La conexión con PostgreSQL funciona.
- El catálogo puede contener cero o más productos activos.

#### Disparador

El visitante accede a la página pública del catálogo.

#### Flujo principal

1. El visitante solicita la página del catálogo.
2. El sistema consulta únicamente los productos activos, pertenecientes a una
   categoría activa y con alguna oferta cuyo tipo de licencia y estado estén
   activos.
3. El sistema carga la categoría y el precio mínimo vigente asociado a cada
   producto sin provocar consultas repetidas.
4. El sistema ordena por nombre e identificador y pagina los resultados en
   bloques de 12.
5. La página muestra los metadatos públicos de cada producto.
6. El visitante puede acceder al detalle de un producto.

#### Flujos alternativos y errores

- FA-01: si no existen productos disponibles, el sistema muestra un estado vacío.
- FA-02: si existen más resultados que el límite de página, se muestra paginación.
- FE-01: si se solicita una página inexistente, el sistema responde con un error 404.

#### Reglas de negocio

- RN-RF01-01: los productos inactivos no aparecen en el catálogo.
- RN-RF01-02: un producto sin categoría activa o sin una oferta activa asociada
  a un tipo de licencia activo no se considera disponible para compra y no
  aparece.
- RN-RF01-03: no es necesario iniciar sesión para consultar el catálogo.
- RN-RF01-04: el archivo sonoro completo nunca se expone públicamente.
- RN-RF01-05: los cambios del catálogo no modifican pedidos anteriores; cuando
  se implemente el pedido, sus líneas conservarán una instantánea de la compra.
- RN-RF01-06: la consulta debe evitar accesos repetidos innecesarios a
  categorías y ofertas de licencia.
- RN-RF01-07: no existe control de stock físico ni decremento de unidades.
- RN-RF01-08: el precio mostrado en la tarjeta es el importe mínimo de las
  ofertas activas y se etiqueta como `Desde` cuando existe más de una.

#### Criterios de aceptación

- CA-RF01-01: dado un producto, su categoría y una oferta de licencia activos,
  cuando un visitante abre el catálogo, entonces el producto aparece.
- CA-RF01-02: dado un producto inactivo, cuando se consulta el catálogo,
  entonces el producto no aparece.
- CA-RF01-03: dado un catálogo vacío, cuando un visitante accede,
  entonces se muestra un mensaje comprensible y no un error.
- CA-RF01-04: dado un catálogo con varias páginas, cuando el usuario cambia
  de página, entonces recibe el bloque de resultados correspondiente.
- CA-RF01-05: cuando se muestra el catálogo, no se publica ninguna URL
  correspondiente al archivo privado completo.
- CA-RF01-06: dado un producto con varias ofertas activas, cuando se muestra su
  tarjeta, entonces aparece el precio mínimo y no un precio ambiguo.
- CA-RF01-07: dado cualquier número de productos en una página, la carga de sus
  categorías y ofertas no aumenta una consulta adicional por cada producto.

#### Datos y permisos

Datos públicos:

- nombre;
- categoría;
- precio;
- moneda;
- duración;
- formato;
- frecuencia de muestreo;
- profundidad de bits;
- resúmenes de las licencias disponibles.

Datos privados:

- archivo completo;
- ruta interna de almacenamiento;
- información administrativa.

El requisito está disponible para usuarios anónimos y autenticados.

#### Pruebas previstas

- El catálogo incluye productos activos.
- El catálogo excluye productos inactivos.
- El catálogo muestra correctamente el estado vacío.
- La paginación devuelve la página solicitada.
- La tarjeta de un producto con varias ofertas activas muestra el importe mínimo,
  su moneda y la etiqueta `Desde`.
- La consulta carga las categorías sin provocar un problema N+1.
- La consulta calcula o precarga las ofertas activas sin provocar un problema
  N+1.
- La respuesta no contiene la URL del archivo completo.

#### Evidencias previstas

- `docs/evidence/RF-01/catalogo-productos-activos.png`
- `docs/evidence/RF-01/catalogo-vacio.png`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Recomendaciones personalizadas.
- Favoritos.
- Suscripciones.
- Descarga desde el catálogo público.
- Edición de productos.

#### Trazabilidad

RF-01 mantiene el estado `Aprobado`; no está completamente verificado porque
CA-RF01-05 tiene su cierre documental pendiente. Desde D-CAT-06 el modelo sí
incluye `master_file` en almacenamiento privado sin URL pública. La entrega
autorizada sigue pendiente de RF-11; en ese hito se revisarán conjuntamente las
evidencias de no exposición y entrega. Esta corrección del 2026-09-27 no declara
el criterio verificado sin completar su trazabilidad.

| Elemento | Referencia |
|---|---|
| Implementación web | `apps/catalog/selectors.py`, `apps/catalog/views.py` y `apps/catalog/templates/catalog/product_list.html` |
| Implementación API | RF-12 |

| Criterio | Prueba | Evidencia | Commit | Estado |
|---|---|---|---|---|
| CA-RF01-01 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-01/CA-RF01-01.md` | `ece0f52` | Verificado |
| CA-RF01-02 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-01/CA-RF01-02.md` | `472ae50` | Verificado: comportamiento preexistente |
| CA-RF01-03 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-01/CA-RF01-03.md` | `5be00ca` | Verificado |
| CA-RF01-04 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-01/CA-RF01-04.md` | `c8e2a20` | Verificado |
| CA-RF01-05 | Revisar cobertura de no exposición existente en catálogo y completar trazabilidad | Cierre documental pendiente | Pendiente de vincular | Pendiente; revisión final con RF-11 |
| CA-RF01-06 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-01/CA-RF01-06.md` | `8415d55` | Verificado |
| CA-RF01-07 | `apps/catalog/tests/test_selectors.py` | `docs/evidence/RF-01/CA-RF01-07.md` | `b2d6eab`, `f3991b7` | Verificado |

### RF-02 — Consultar detalle y escuchar una preview pública

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Must |
| Versión objetivo | v0.2.0 |
| Estado | Aprobado |
| Dependencias | RF-01, RNF-01, RNF-03 a RNF-07, RNF-09 y RNF-11 |

#### Objetivo

Permitir que cualquier visitante comprenda las características técnicas y el
alcance de las licencias de un producto activo y escuche una preview pública
sin obtener acceso al archivo maestro.

#### Precondiciones

- El producto, su categoría, al menos una oferta y el tipo de licencia de esa
  oferta están activos.
- Existe un `slug` público y único para el producto.
- Existe una preview pública y es un archivo distinto del maestro.

#### Disparador

El visitante selecciona un producto desde el catálogo o solicita su URL de
detalle.

#### Flujo principal

1. El sistema localiza el producto activo por su `slug`.
2. El sistema carga su categoría y las ofertas activas asociadas a tipos de
   licencia activos.
3. La página muestra nombre, descripción, duración, formato del archivo
   adquirido, frecuencia de muestreo y profundidad de bits.
4. La página muestra cada licencia disponible, su plataforma o destino de uso,
   su resumen, precio y moneda.
5. La página ofrece un reproductor para la preview pública.
6. El visitante puede volver al catálogo sin autenticarse.

#### Flujos alternativos y errores

- FA-01: si la preview está temporalmente no disponible, el detalle permanece
  consultable, muestra un aviso y nunca usa el archivo maestro como sustituto.
- FE-01: si el `slug` no existe, el sistema responde con 404.
- FE-02: si el producto, su categoría, todas sus ofertas o todos los tipos de
  licencia asociados están inactivos, el sistema responde con 404 aunque el
  visitante conozca la URL anterior.

#### Reglas de negocio

- RN-RF02-01: el detalle es público para usuarios anónimos y autenticados.
- RN-RF02-02: solo se muestran ofertas activas asociadas a tipos de licencia
  activos.
- RN-RF02-03: una licencia expresa un destino de uso; no representa el sistema
  operativo desde el que se descarga el archivo.
- RN-RF02-04: la preview es un archivo promocional separado, preparado antes de
  su carga y sin relación pública con la ruta del archivo maestro.
- RN-RF02-05: el fallo o ausencia de la preview nunca habilita el maestro.
- RN-RF02-06: el archivo maestro, su ruta y cualquier URL de descarga quedan
  excluidos del contexto público.
- RN-RF02-07: un producto no debe activarse para publicación sin una preview
  configurada; FA-01 cubre una indisponibilidad operativa posterior.

#### Criterios de aceptación

- CA-RF02-01: dado un producto disponible, cuando se abre su detalle, entonces
  se muestran sus metadatos técnicos y sus ofertas de licencia activas.
- CA-RF02-02: dado un visitante anónimo, cuando reproduce la preview, entonces
  obtiene únicamente el archivo público preparado para preview.
- CA-RF02-03: dado un `slug` inexistente o un producto no disponible, cuando se
  solicita su detalle, entonces la respuesta es 404.
- CA-RF02-04: dada una oferta de licencia inactiva, cuando se abre el detalle,
  entonces esa oferta no aparece.
- CA-RF02-05: dada una preview ausente, cuando se abre el detalle, entonces se
  informa de su indisponibilidad y no se expone el archivo maestro.
- CA-RF02-06: el HTML y el contexto del detalle no contienen la ruta ni la URL
  del archivo completo.

#### Datos y permisos

Datos públicos:

- nombre, `slug`, categoría y descripción;
- duración, formato, frecuencia de muestreo y profundidad de bits;
- URL del archivo de preview pública;
- nombre, destino, resumen, precio y moneda de cada licencia activa.

Datos privados:

- SKU interno;
- archivo maestro y ubicación de almacenamiento;
- notas y metadatos administrativos.

No se requiere autenticación. Los métodos de modificación no forman parte de
la interfaz pública.

#### Pruebas previstas

- El detalle de un producto disponible responde 200.
- Un producto inexistente, inactivo o no vendible responde 404.
- Solo aparecen ofertas activas.
- El reproductor referencia la preview pública.
- Si falta la preview, no se utiliza el maestro como alternativa.
- La respuesta no contiene el nombre, la ruta ni la URL del archivo maestro.

#### Evidencias previstas

- `docs/evidence/RF-02/detalle-producto-preview.png`
- `docs/evidence/RF-02/producto-no-disponible-404.png`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Descarga del archivo comprado.
- Generación o transcodificación automática de previews.
- Forma de onda interactiva, favoritos y recomendaciones.
- Compra, carrito o selección definitiva de licencia.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | `apps/catalog/tests/test_views.py` |
| Implementación web | `apps/catalog/urls.py`, `apps/catalog/views.py` y `apps/catalog/templates/catalog/product_detail.html` |
| Consulta compartida | `apps/catalog/selectors.py:get_available_products()` |
| Implementación API | RF-12 |
| Evidencia | `docs/evidence/RF-02/` y `docs/technical-log.md` |
| Commits | `5a7c1cf` a `20e9747` |

| Criterio | Prueba | Evidencia | Commit | Estado |
|---|---|---|---|---|
| CA-RF02-01 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-02/CA-RF02-01.md` | `5a7c1cf` | Verificado |
| CA-RF02-02 | `apps/catalog/tests/test_views.py` | `docs/technical-log.md` | `01714b6`, `20e9747` | Verificado |
| CA-RF02-03 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-02/CA-RF02-03.md` | `bd4b913`, `954f535` | Verificado: comportamiento preexistente |
| CA-RF02-04 | `apps/catalog/tests/test_views.py` | `docs/evidence/RF-02/CA-RF02-04.md` | `b77ef70` | Verificado: comportamiento preexistente |
| CA-RF02-05 | `apps/catalog/tests/test_views.py` | `docs/technical-log.md` | `1125c4b` | Verificado |
| CA-RF02-06 | `apps/catalog/tests/test_views.py` | `docs/technical-log.md` | `bb599cd` | Verificado |

### RF-03 — Buscar, filtrar, ordenar y paginar el catálogo

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Should |
| Versión objetivo | v0.2.0 |
| Estado | Verificado |
| Dependencias | RF-01, RF-02, RNF-03 a RNF-05, RNF-07, RNF-09 y RNF-11 |

#### Estado de preparación

Los conflictos previos quedaron cerrados el 2026-09-01:

- contrato y alcance aprobados en `3e30a7c`;
- ofertas asociadas a tipos de licencia inactivos excluidas en `3c58ae7`;
- carga de `license_type` sin N+1 verificada en `f3991b7`;
- trazabilidad previa consolidada en `9674d9b`.

Los siete criterios (CA-RF03-01 a CA-RF03-07) están verificados. El código
procesa `q`, `category`, `license` y `ordering`; valida los parámetros
conocidos y responde 400 ante valores inválidos; pagina y conserva el estado
de consulta; y la plantilla mantiene visibles los controles con sus valores
reconocidos. CA-RF03-01 a CA-RF03-06 cuentan con evidencia individual y los
commits de comportamiento correspondientes.

#### Objetivo

Permitir que el visitante reduzca y ordene el catálogo público mediante un
contrato de consulta limitado, comprensible y reutilizable por la web y la API.

#### Contrato de consulta aprobado

| Parámetro | Finalidad | Valores admitidos |
|---|---|---|
| `q` | Buscar en nombre, resumen y descripción | Texto normalizado de hasta 100 caracteres |
| `category` | Filtrar categoría | `slug` de categoría activa o valor vacío |
| `license` | Filtrar destino de licencia | `slug` de licencia activa o valor vacío |
| `ordering` | Ordenar | `name`, `-name`, `price`, `-price` |
| `page` | Seleccionar página | Entero positivo |

#### Precondiciones

- RF-01 está disponible.
- Los filtros se aplican siempre sobre el conjunto de productos disponibles,
  nunca sobre productos administrativos o inactivos.

#### Disparador

El visitante envía uno o varios parámetros desde los controles del catálogo.

#### Flujo principal

1. El sistema elimina espacios exteriores y agrupa espacios interiores
   consecutivos del texto de búsqueda.
2. El sistema valida los parámetros públicos conocidos; los desconocidos se
   ignoran y nunca se convierten en expresiones ORM ni se propagan al paginar.
3. El sistema parte de la consulta pública definida por RF-01.
4. El sistema aplica búsqueda y filtros combinándolos mediante una condición
   lógica `AND`.
5. El sistema aplica exclusivamente un orden permitido y añade el identificador
   como desempate estable.
6. El sistema pagina 12 productos y conserva los filtros al cambiar de página.
7. La página mantiene visibles los controles y sus valores activos.

#### Flujos alternativos y errores

- FA-01: una búsqueda sin coincidencias muestra un estado vacío contextual.
- FA-02: `q` vacío equivale a no aplicar búsqueda.
- FA-03: `category` o `license` vacíos equivalen a no aplicar ese filtro.
- FE-01: un valor inválido de un parámetro conocido responde 400 y señala el
  parámetro, sin incluir detalles internos.
- FE-02: una página inexistente, no numérica o menor que uno responde 404.

#### Reglas de negocio

- RN-RF03-01: los filtros nunca permiten recuperar un producto no disponible.
- RN-RF03-02: la búsqueda no distingue mayúsculas de minúsculas y compara la
  frase normalizada con `name`, `summary` y `description` mediante una condición
  lógica `OR`.
- RN-RF03-03: ordenar por precio utiliza el mínimo de todas las ofertas públicas
  del producto, es decir, ofertas activas asociadas a tipos de licencia activos.
  El filtro de licencia comprueba que el producto ofrece ese destino, pero no
  sustituye el precio global mostrado como `Desde` por el de la licencia filtrada.
- RN-RF03-04: los valores de ordenación pertenecen a una lista cerrada; no se
  convierten parámetros del usuario directamente en expresiones ORM.
- RN-RF03-05: el orden siempre es determinista para impedir duplicados o saltos
  entre páginas.
- RN-RF03-06: web y API reutilizan la misma construcción de consulta, aunque
  cada interfaz valide y represente sus errores en su propia capa HTTP.
- RN-RF03-07: RF-03 implementa primero la interfaz web `/catalog/`; RF-12
  reutiliza después la consulta aprobada para la API DRF.
- RN-RF03-08: un `slug` inexistente o inactivo en `category` o `license` es un
  valor conocido inválido y responde 400; un valor vacío omite el filtro.

#### Criterios de aceptación

- CA-RF03-01: dada una palabra o frase normalizada contenida en `name`, `summary`
  o `description`, cuando se busca sin distinguir mayúsculas de minúsculas,
  entonces solo aparecen productos disponibles coincidentes.
- CA-RF03-02: dados los `slug` de una categoría y un tipo de licencia activos,
  cuando se combinan ambos filtros, entonces solo aparecen productos disponibles
  de esa categoría que poseen una oferta pública para esa licencia.
- CA-RF03-03: cuando se ordena por `price` o `-price`, entonces se utiliza el
  precio mínimo global de las ofertas y tipos de licencia activos y se añade el
  identificador como desempate estable.
- CA-RF03-04: cuando se cambia de página, entonces se conservan únicamente `q`,
  `category`, `license` y `ordering`, y solo se sustituye el valor de `page`.
- CA-RF03-05: dada una consulta válida sin coincidencias, entonces la respuesta
  es 200, se muestra un mensaje comprensible y se conservan visibles los
  controles con sus valores reconocidos.
- CA-RF03-06: dado un valor no permitido en `ordering`, o un `slug` inexistente
  o inactivo en `category` o `license`, entonces la respuesta es 400, identifica
  ese parámetro sin detalles internos y no ejecuta una ordenación construida
  con el texto recibido. Si además la página solicitada fuera inválida, la
  respuesta sigue siendo 400 (FE-01 tiene precedencia sobre FE-02).
- CA-RF03-07: dada una página posterior a la última, no numérica o menor que uno,
  entonces la respuesta es 404; la página 1 de una consulta válida vacía
  responde 200.

#### Pruebas previstas

- Búsqueda por nombre y descripción sin distinguir mayúsculas.
- Combinación de categoría y licencia.
- Exclusión de productos, categorías, ofertas y tipos de licencia inactivos.
- Rechazo de categorías y licencias inexistentes o inactivas.
- Cada opción permitida de ordenación y su desempate estable.
- Rechazo de valores de ordenación no permitidos.
- Persistencia de parámetros en enlaces de paginación.
- Estado vacío contextual y página inexistente.
- Número acotado de consultas al combinar relaciones y paginación.

#### Limitaciones de cobertura conocidas

- Ninguna prueba combina un filtro `license` activo con varias ofertas de
  precio distinto para comprobar explícitamente que el precio `Desde`
  mostrado sigue siendo el mínimo global (D-RF03-05); solo existe una prueba
  general de precio mínimo sin filtro, heredada de RF-02.
- La prueba de número acotado de consultas
  (`apps/catalog/tests/test_selectors.py::test_available_product_relations_use_a_constant_number_of_queries`)
  solo ejercita `get_available_products()` sin combinar búsqueda, filtros y
  orden a la vez.

#### Evidencias previstas

- `docs/evidence/RF-03/catalogo-filtrado.png`
- `docs/evidence/RF-03/catalogo-sin-resultados.png`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Autocompletado, tolerancia a errores ortográficos y búsqueda semántica.
- Etiquetas múltiples, géneros jerárquicos y recomendaciones. La propuesta de
  familias y subfamilias se especifica separadamente en RF-16; no forma parte
  del contrato verificado original de RF-03.
- Filtros por formato, frecuencia de muestreo y profundidad de bits.
- Ordenación por popularidad o comportamiento del usuario.
- Tamaño de página configurable por el consumidor.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | `apps/catalog/tests/test_views.py` y `apps/catalog/tests/test_selectors.py`; CA-RF03-07 reutiliza pruebas de RF-01 |
| Decisiones aplicables | `docs/requirements/rf03-decision-checkpoint.md`, commit `3e30a7c` |
| Selector base disponible | `apps/catalog/selectors.py:get_available_products()`, `get_active_categories()`, `get_active_license_types()`, `ORDERING_OPTIONS` |
| Implementación web | `apps/catalog/views.py:product_list()` (búsqueda, filtros, orden, validación 400, conservación de estado) y `apps/catalog/templates/catalog/product_list.html` (controles visibles) |
| Consulta compartida | `apps/catalog/selectors.py:get_available_products()` |
| Implementación API | RF-12 |
| Evidencia | Puerta de calidad en `docs/evidence/RF-03/quality-gate-2026-09-01.md`; evidencias individuales `CA-RF03-01.md` a `CA-RF03-07.md` en `docs/evidence/RF-03/` |
| Commits de preparación | `3e30a7c`, `3c58ae7`, `f3991b7`, `9674d9b` |
| Commits de implementación | `3e52b90` (CA-RF03-01) y `df1f52e` (CA-RF03-02 a CA-RF03-06) |

| Criterio | Prueba | Evidencia | Commit | Estado |
|---|---|---|---|---|
| CA-RF03-01 | `apps/catalog/tests/test_views.py::test_catalog_searches_available_products_by_normalized_text_case_insensitively` | `docs/evidence/RF-03/CA-RF03-01.md` | `3e52b90` | Verificado |
| CA-RF03-02 | `apps/catalog/tests/test_views.py::test_catalog_filters_available_products_by_category_and_license_slug` | `docs/evidence/RF-03/CA-RF03-02.md` | `df1f52e` | Verificado |
| CA-RF03-03 | `apps/catalog/tests/test_views.py::test_catalog_orders_available_products_by_minimum_price_with_stable_tiebreak` | `docs/evidence/RF-03/CA-RF03-03.md` | `df1f52e` | Verificado |
| CA-RF03-04 | `apps/catalog/tests/test_views.py::test_catalog_pagination_link_preserves_only_search_filters_and_ordering` | `docs/evidence/RF-03/CA-RF03-04.md` | `df1f52e` | Verificado |
| CA-RF03-05 | `apps/catalog/tests/test_views.py::test_catalog_renders_category_and_license_selects_with_active_options_and_recognized_value`, `test_catalog_shows_message_and_keeps_all_recognized_controls_visible_when_query_has_no_matches` | `docs/evidence/RF-03/CA-RF03-05.md` | `df1f52e` | Verificado |
| CA-RF03-06 | `apps/catalog/tests/test_views.py::test_catalog_returns_400_for_an_unrecognized_ordering_value`, `test_catalog_orders_available_products_by_name_in_descending_order`, `test_catalog_returns_400_for_an_unrecognized_category_slug`, `test_catalog_returns_400_for_an_unrecognized_license_slug`, `test_catalog_returns_400_instead_of_404_when_an_invalid_category_and_an_invalid_page_are_combined` | `docs/evidence/RF-03/CA-RF03-06.md` | `df1f52e` | Verificado |
| CA-RF03-07 | `apps/catalog/tests/test_views.py` (pruebas 404/200 reutilizadas de RF-01) | `docs/evidence/RF-03/CA-RF03-07.md` | `c8e2a20` | Verificado: Green preexistente de RF-01 |

Nota resuelta: la validación de `category`/`license` inválidos (RN-RF03-08) y
la precedencia de FE-01 sobre FE-02 quedan registradas como parte del texto
ampliado de CA-RF03-06 (ver arriba), no como un criterio nuevo.

CA-RF03-07 reutiliza la paginación y las pruebas 404 implementadas por RF-01;
no se revierte comportamiento correcto para fabricar un Red. El 2026-09-02 se
ejecutaron las pruebas objetivo de CA-RF03-01 a CA-RF03-06, la regresión de
vistas y selectores (`34 passed`) y la suite completa (`86 passed`). Cada
criterio cuenta con evidencia individual y referencia a un commit de
comportamiento, por lo que RF-03 pasa a `Verificado`. La validación de
`category` y `license` inválidos, así como la precedencia 400 sobre 404, están
resueltas como ampliación de CA-RF03-06 por D-RF03-10. Se mantienen las dos
limitaciones de cobertura declaradas arriba.

### RF-04 — Registrarse, iniciar sesión y cerrar sesión

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Must |
| Versión objetivo | v0.3.0 |
| Estado | Verificado |
| Dependencias | RNF-01, RNF-03, RNF-04, RNF-10 y RNF-11 |

#### Objetivo

Permitir que un visitante cree una cuenta y que un cliente inicie y cierre una
sesión web segura mediante la autenticación de Django.

#### Contrato web implementado

| Operación | Ruta | Métodos | Resultado |
|---|---|---|---|
| Registro | `/accounts/register/` | `GET`, `POST` | Formulario o creación de cuenta |
| Inicio de sesión | `/accounts/login/` | `GET`, `POST` | Formulario o sesión autenticada |
| Cierre de sesión | `/accounts/logout/` | `POST` | Fin de sesión y redirección para un cliente autenticado; `403` sin modificar la sesión para un visitante anónimo |

El identificador de acceso es `username`. El registro solicita `username`,
`password1` y `password2`; el correo electrónico no es obligatorio para el MVP.
Tras un registro válido, el usuario queda autenticado y se redirige al catálogo.
El destino predeterminado después de iniciar o cerrar sesión también es el
catálogo.

#### Precondiciones

- La aplicación y PostgreSQL están disponibles.
- El modelo personalizado `users.User` está configurado como `AUTH_USER_MODEL`.
- Las sesiones, CSRF y el middleware de autenticación de Django están activos.

#### Disparador

Un visitante abre el formulario de registro o inicio de sesión, o un cliente
autenticado solicita cerrar su sesión.

#### Flujo principal

1. El visitante abre el formulario de registro.
2. El sistema valida el nombre de usuario y las dos contraseñas con las reglas
   de Django.
3. El sistema crea un usuario ordinario con la contraseña cifrada mediante el
   hasher configurado.
4. El sistema inicia la sesión y redirige al catálogo.
5. En accesos posteriores, el cliente puede iniciar sesión con `username` y
   contraseña.
6. El cliente puede cerrar la sesión mediante un formulario `POST` protegido
   por CSRF.

#### Flujos alternativos y errores

- FA-01: un usuario ya autenticado que solicita registro o login es redirigido
  al catálogo sin modificar su identidad ni su sesión.
- FA-02: después de un login válido, un parámetro `next` interno y seguro tiene
  prioridad sobre el destino predeterminado.
- FE-01: un nombre de usuario duplicado, contraseñas distintas o una contraseña
  inválida vuelven a mostrar el formulario sin crear usuario ni sesión.
- FE-02: unas credenciales incorrectas muestran un error genérico y no revelan
  si el nombre de usuario existe.
- FE-03: un `next` externo o inseguro se ignora y se usa el catálogo.
- FE-04: una solicitud `GET` sobre el cierre de sesión no modifica la sesión y
  responde 405.
- FE-05: un visitante anónimo que envía un `POST` con CSRF válido al cierre de
  sesión recibe 403 y su sesión no se crea, vacía, rota ni invalida.

#### Reglas de negocio

- RN-RF04-01: la autenticación web usa sesiones de Django; la autenticación de
  la API privada se definirá en RF-13.
- RN-RF04-02: el nombre de usuario es el identificador único de acceso durante
  el MVP.
- RN-RF04-03: las contraseñas se validan y almacenan exclusivamente mediante
  las utilidades de autenticación de Django.
- RN-RF04-04: el registro nunca concede `is_staff`, `is_superuser` ni permisos
  de modelo.
- RN-RF04-05: solo se aceptan redirecciones `next` internas y seguras.
- RN-RF04-06: cerrar sesión requiere `POST` y protección CSRF.
- RN-RF04-07: los errores de login no permiten enumerar usuarios.
- RN-RF04-08: registro y login no sustituyen la identidad de una sesión que ya
  está autenticada.
- RN-RF04-09: un `POST` con CSRF válido al cierre de sesión requiere un cliente
  autenticado; si procede de un visitante anónimo, responde 403 sin modificar
  su sesión.

#### Criterios de aceptación

- CA-RF04-01: dado un visitante anónimo, cuando abre registro o login, entonces
  recibe 200 y un formulario protegido por CSRF.
- CA-RF04-02: dados un `username` disponible y contraseñas válidas coincidentes,
  cuando el visitante se registra, entonces se crea un usuario activo, no
  privilegiado, se inicia su sesión y se le redirige al catálogo.
- CA-RF04-03: dado un registro válido, cuando se consulta el usuario persistido,
  entonces la contraseña no está en texto plano y `check_password()` la valida.
- CA-RF04-04: dado un nombre duplicado, contraseñas distintas o una contraseña
  rechazada por los validadores, cuando se envía el registro, entonces no se
  crea usuario ni sesión y se muestran errores comprensibles.
- CA-RF04-05: dadas credenciales correctas, cuando el visitante inicia sesión,
  entonces se crea la sesión y se le redirige a un `next` interno válido o al
  catálogo si no existe.
- CA-RF04-06: dadas credenciales incorrectas, cuando se intenta iniciar sesión,
  entonces el usuario permanece anónimo y recibe un error genérico.
- CA-RF04-07: dado un `next` externo o inseguro, cuando el login es correcto,
  entonces el sistema no abandona Foleyra y redirige al catálogo.
- CA-RF04-08: dado un cliente autenticado, cuando envía un `POST` válido al
  cierre de sesión, entonces la sesión termina; dado un visitante anónimo que
  envía ese `POST` con CSRF válido, entonces recibe 403 sin modificar su
  sesión; un `GET` no la modifica y responde 405.
- CA-RF04-09: dado un cliente autenticado, cuando abre registro o login,
  entonces se le redirige al catálogo sin crear otra identidad ni sustituir su
  sesión.

#### Datos y permisos

Datos de entrada:

- nombre de usuario;
- contraseña y confirmación durante el registro;
- contraseña durante el login;
- destino interno opcional `next`.

Datos privados:

- hash de contraseña;
- identificador y contenido de la sesión;
- credenciales introducidas en los formularios.

Registro y login son accesibles únicamente para visitantes anónimos. El cierre
de sesión solo produce efecto para un cliente autenticado y requiere `POST`.
Un visitante anónimo con un `POST` y CSRF válidos recibe 403 sin modificar su
sesión.

#### Matriz de implementación

| Criterio | Comportamiento | Prueba | Componentes afectados | Estado |
|---|---|---|---|---|
| CA-RF04-01 | Formularios públicos con CSRF | `test_anonymous_visitor_receives_a_csrf_protected_authentication_form` | URLs, vistas, formularios y plantillas de usuarios | Verificado |
| CA-RF04-02 | Alta ordinaria e inicio automático de sesión | `test_anonymous_visitor_can_register_as_an_active_unprivileged_user` | Modelo `User`, formulario y vista de registro | Verificado |
| CA-RF04-03 | Contraseña almacenada mediante hash | `test_registered_user_password_is_hashed` | Formulario de registro y modelo `User` | Verificado |
| CA-RF04-04 | Rechazo de registros inválidos sin efectos parciales | `test_invalid_registration_does_not_create_a_user_or_session` | Formulario y vista de registro | Verificado |
| CA-RF04-05 | Login válido y redirección interna | `test_anonymous_visitor_can_log_in_with_a_safe_internal_destination` | Vista de login y configuración de autenticación | Verificado |
| CA-RF04-06 | Error genérico sin sesión | `test_invalid_credentials_show_a_generic_error_without_a_session` | Formulario y plantilla de login | Verificado |
| CA-RF04-07 | Rechazo de redirecciones externas | `test_login_ignores_an_external_or_unsafe_next_url` | Vista de login | Verificado |
| CA-RF04-08 | Logout exclusivamente por POST | Pruebas de logout en `apps/users/tests/test_views.py` | Vista, URL y navegación base | Verificado |
| CA-RF04-09 | Sesión existente preservada | `test_authenticated_user_is_redirected_from_authentication_forms` | Vistas de autenticación | Verificado |

#### Pruebas implementadas

- `apps/users/tests/test_views.py` cubre CA-RF04-01 a CA-RF04-09, incluido el
  formulario CSRF de logout en la navegación para sesiones autenticadas.
- `apps/users/tests/test_user_model.py` comprueba la persistencia de
  `users.User` y la validación de su hash de contraseña.
- La ejecución focalizada más reciente de `apps/users/tests/test_views.py`
  finalizó con 21 pruebas superadas.

#### Migraciones

RF-04 no requiere una migración nueva: reutiliza `users.User`, definido en
`apps/users/migrations/0001_initial.py`, sin cambios de esquema.

#### Evidencias

Las capturas `docs/evidence/RF-04/registro-valido.png` y
`docs/evidence/RF-04/login-y-logout.png` registran los flujos web de registro
válido y de login seguido de logout. La puerta de calidad posterior a la
corrección de Ruff está consolidada en
`docs/evidence/RF-04/quality-gate-2026-09-02.md`.

#### Fuera de alcance

- Verificación y activación por correo electrónico.
- Recuperación o cambio de contraseña mediante correo.
- Autenticación multifactor, social o sin contraseña.
- Autenticación por token para la API.
- Perfiles públicos y edición de datos personales.

#### Trazabilidad

RF-04 está `Verificado`: las rutas web se registran en `config/urls.py`, las
vistas y formularios residen en `apps/users/`, y la cobertura de integración se
concentra en `apps/users/tests/test_views.py`. La autenticación para API
privada permanece diferida a RF-13. Las evidencias y la puerta de calidad están
registradas en `docs/evidence/RF-04/quality-gate-2026-09-02.md`. El commit de
trazabilidad es `9a30310` (`feat(users): add web authentication flows`).

El `POST` anónimo con CSRF válido al cierre de sesión queda definido como una
ampliación de CA-RF04-08: responde 403 y no modifica la sesión. No constituye
un criterio adicional ni altera las rutas, actores o alcance aprobados.

### RF-05 — Gestionar productos del carrito privado

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Cliente autenticado |
| Prioridad | Must |
| Versión objetivo | v0.3.0 |
| Estado | Aprobado |
| Dependencias | RF-01, RF-02, RF-04, RNF-01, RNF-03 a RNF-06, RNF-08, RNF-10 y RNF-11 |

#### Objetivo

Permitir que un cliente autenticado mantenga una selección privada de ofertas
concretas de producto y licencia antes de convertirla en pedido mediante RF-06.

#### Contrato web aprobado

| Operación | Ruta | Métodos | Resultado |
|---|---|---|---|
| Consultar carrito propio | `/cart/` | `GET` | Carrito actual o estado vacío |
| Añadir oferta | `/cart/items/add/` | `POST` | Línea añadida o conservada sin duplicar |
| Eliminar línea | `/cart/items/{line_id}/remove/` | `POST` | Línea eliminada y total recalculado |

La operación de alta recibe el identificador de una `ProductLicenseOffer`, no
el identificador aislado de un producto. Cada línea representa una licencia
concreta para un producto y tiene cantidad implícita igual a uno.

#### Decisiones operativas aprobadas

- `GET /cart/` anónimo se redirige al login con un `next` interno; un `GET`
  sobre alta o eliminación responde `405` para cualquier usuario. Esta regla
  específica prevalece sobre la redirección general de CA-RF05-01.
- Un `POST` anónimo con CSRF válido se redirige al login con `next=/cart/` sin
  consultar ni modificar el carrito; un `POST` sin CSRF válido responde `403`.
- Las altas y eliminaciones correctas usan PRG y redirigen a `/cart/`. La
  interfaz informa de forma distinguible si la oferta se añadió o ya estaba
  incluida.
- Un `offer_id` ausente o malformado responde `400`; una oferta numérica
  inexistente o no disponible responde `404`. Una línea inexistente o ajena
  responde `404`.
- El carrito es una selección actual única por usuario, sin estado ni
  historial. RF-06 creará el pedido histórico y vaciará sus líneas en su misma
  transacción, conservando el carrito como selección vacía.
- El carrito se relaciona uno a uno con su propietario y sus líneas se borran
  con él. Las líneas referencian ofertas con `PROTECT` y PostgreSQL garantiza
  una sola línea por `(cart, offer)`; una carrera de unicidad se interpreta como
  oferta ya incluida.
- El identificador de oferta puede incluirse solo como campo oculto en el
  formulario autenticado; no se publica como dato de catálogo ni se incorpora a
  la API pública.
- RF-05 crea y prueba el servicio compartido. La equivalencia completa de
  CA-RF05-12 queda pendiente hasta que RF-13 sea aprobado e implemente su API;
  RF-05 no añade endpoints API ni cambios administrativos.

#### Precondiciones

- El cliente está autenticado mediante RF-04.
- El catálogo y sus reglas de disponibilidad están operativos.
- La oferta que se añade identifica un producto y un tipo de licencia concretos.

#### Disparador

El cliente consulta su carrito, añade una oferta desde el detalle del producto
o elimina una línea existente.

#### Flujo principal

1. El cliente selecciona una oferta de licencia en el detalle de un producto.
2. El sistema comprueba la identidad del cliente y la disponibilidad actual de
   producto, categoría, oferta y tipo de licencia.
3. El servicio obtiene o crea el único carrito abierto del cliente.
4. El servicio añade una única línea para la oferta seleccionada.
5. El carrito muestra producto, licencia, alcance, precio actual, moneda y total.
6. El cliente puede eliminar una línea propia mediante `POST`.

#### Flujos alternativos y errores

- FA-01: un cliente sin carrito o sin líneas ve un estado vacío y la consulta
  `GET` no crea datos innecesarios.
- FA-02: si la oferta ya está incluida, la operación conserva una única línea e
  informa de que ya estaba en el carrito.
- FA-03: dos licencias distintas para el mismo producto se conservan como líneas
  diferentes.
- FA-04: si cambia el precio de una oferta, la siguiente consulta muestra el
  precio y el total actuales.
- FA-05: si una oferta añadida deja de estar disponible, la línea permanece
  visible como no disponible, se excluye del total comprable y puede eliminarse.
- FE-01: un visitante anónimo es redirigido al login con un `next` interno y no
  se modifica ningún dato.
- FE-02: una oferta inexistente o no disponible no se añade y responde 404.
- FE-03: una línea inexistente o perteneciente a otro usuario responde 404 y no
  revela su existencia.
- FE-04: una solicitud `GET` sobre una operación de escritura responde 405 y no
  modifica el carrito.

#### Reglas de negocio

- RN-RF05-01: cada cliente puede tener como máximo un carrito abierto.
- RN-RF05-02: una línea referencia una `ProductLicenseOffer`; no referencia solo
  un producto ni copia todavía datos históricos.
- RN-RF05-03: una oferta aparece como máximo una vez en el mismo carrito y su
  cantidad implícita es uno.
- RN-RF05-04: el mismo producto puede aparecer con tipos de licencia distintos.
- RN-RF05-05: solo se pueden añadir ofertas cuyo producto, categoría, oferta y
  tipo de licencia estén activos.
- RN-RF05-06: los precios y totales del carrito son valores actuales calculados
  con `Decimal`; RF-06 creará la instantánea histórica al generar el pedido.
- RN-RF05-07: una oferta sobrevenida como no disponible no se elimina en
  silencio ni forma parte del total comprable.
- RN-RF05-08: todas las consultas y mutaciones se limitan al carrito del usuario
  autenticado; una referencia ajena se trata como inexistente.
- RN-RF05-09: las escrituras usan `POST`, protección CSRF y un servicio de
  negocio compartible con RF-13.
- RN-RF05-10: el carrito no maneja stock, suscripciones, cantidades editables,
  impuestos, envío, cupones ni múltiples monedas.

#### Criterios de aceptación

- CA-RF05-01: dado un visitante anónimo, cuando intenta consultar o modificar el
  carrito, entonces es redirigido al login con un `next` interno y ningún dato
  cambia.
- CA-RF05-02: dado un cliente autenticado sin carrito ni líneas, cuando consulta
  el carrito, entonces recibe 200 y ve un estado vacío sin crear datos mediante
  la petición `GET`.
- CA-RF05-03: dada una oferta cuyo producto, categoría, licencia y propia oferta
  están activos, cuando el cliente la añade mediante `POST`, entonces aparece
  una línea asociada a esa oferta en su único carrito abierto.
- CA-RF05-04: dada una oferta ya incluida, cuando el cliente vuelve a añadirla,
  entonces el carrito conserva una sola línea con cantidad implícita uno.
- CA-RF05-05: dado un producto con dos ofertas de licencia distintas, cuando el
  cliente añade ambas, entonces aparecen como dos líneas diferenciadas.
- CA-RF05-06: dada una oferta inexistente o no disponible, cuando se intenta
  añadir, entonces la respuesta es 404 y el carrito no cambia.
- CA-RF05-07: dado un carrito con líneas disponibles, cuando se consulta,
  entonces muestra producto, licencia, alcance, precio actual, moneda y un total
  calculado con importes decimales.
- CA-RF05-08: dado un cambio de precio anterior al checkout, cuando se vuelve a
  consultar el carrito, entonces se muestran el precio y el total actuales sin
  crear todavía una instantánea histórica.
- CA-RF05-09: dada una oferta que deja de estar disponible después de añadirse,
  cuando se consulta el carrito, entonces su línea aparece como no disponible,
  queda excluida del total comprable y puede eliminarse.
- CA-RF05-10: dada una línea propia, cuando el cliente la elimina mediante
  `POST`, entonces desaparece y el total se recalcula; un `GET` no modifica el
  carrito.
- CA-RF05-11: dados dos clientes, cuando uno intenta consultar, eliminar o
  modificar una línea del otro, entonces recibe 404 y los datos ajenos no
  cambian.
- CA-RF05-12: dadas las mismas condiciones de dominio, las entradas web de
  RF-05 y la futura API de RF-13 usan el mismo servicio y producen la misma
  transición del carrito.

#### Datos y permisos

Datos visibles para el propietario:

- nombre y `slug` del producto;
- nombre, alcance y versión actual del tipo de licencia;
- precio actual y moneda de la oferta;
- disponibilidad actual de la línea;
- total comprable del carrito.

Datos internos:

- identificadores de carrito, línea y oferta;
- propietario del carrito;
- fechas técnicas de creación o modificación.

El carrito es privado. Un usuario solo puede consultar o modificar su propio
carrito y sus propias líneas.

#### Matriz de implementación prevista

| Criterio | Comportamiento | Prueba prevista | Componentes afectados | Riesgos |
|---|---|---|---|---|
| CA-RF05-01 | Acceso privado sin escrituras anónimas | GET y POST sin sesión | Vistas, URLs y RF-04 | Modificación anónima |
| CA-RF05-02 | Estado vacío sin escritura por GET | Consulta repetida sin carrito | Vista, selector y plantilla | Datos creados al leer |
| CA-RF05-03 | Alta de una oferta disponible | POST y comprobación de propietario y oferta | Modelos y servicio de carrito, catálogo | Línea sin licencia concreta |
| CA-RF05-04 | Alta repetida sin duplicados | Dos POST y recuento de líneas | Servicio y restricciones PostgreSQL | Duplicados o carrera |
| CA-RF05-05 | Licencias distintas como líneas distintas | Dos ofertas del mismo producto | Modelo y servicio de carrito | Identidad de línea incorrecta |
| CA-RF05-06 | Rechazo uniforme de indisponibilidad | Producto, categoría, oferta y licencia inactivos | Selector y servicio compartido | Divergencia con el catálogo |
| CA-RF05-07 | Presentación y total decimal | Varias líneas y suma esperada | Selector, plantilla y oferta | Totales erróneos o N+1 |
| CA-RF05-08 | Precio actual hasta checkout | Cambio de precio y segunda consulta | Selector y catálogo | Expectativa de precio reservado |
| CA-RF05-09 | Línea sobrevenida no disponible | Desactivación después del alta | Selector, plantilla y futuro RF-06 | Checkout inválido o desaparición silenciosa |
| CA-RF05-10 | Eliminación propia exclusivamente por POST | POST propio y GET sobre la operación | Vista, servicio y URLs | CSRF o mutación por GET |
| CA-RF05-11 | Aislamiento estricto por propietario | Intentos cruzados entre dos clientes | Selector, servicio y vista | IDOR y fuga de datos |
| CA-RF05-12 | Regla compartida con la futura API | Prueba de servicio y posterior equivalencia | Servicio de carrito y RF-13 | Reglas duplicadas web/API |

#### Pruebas previstas

- Acceso anónimo y autenticado al carrito.
- Estado vacío sin efectos laterales de lectura.
- Creación de un único carrito abierto por usuario.
- Alta de una oferta disponible y rechazo de cada condición de indisponibilidad.
- Repetición de la misma alta y protección persistente frente a duplicados.
- Dos licencias distintas para un mismo producto.
- Presentación, suma decimal y actualización de precios actuales.
- Tratamiento de una línea que deja de estar disponible.
- Eliminación por `POST` y rechazo de mutaciones por `GET`.
- Aislamiento completo entre propietarios.
- Pruebas del servicio independientes de la vista para permitir su reutilización
  en RF-13.

#### Evidencias previstas

- `docs/evidence/RF-05/carrito-vacio.png`
- `docs/evidence/RF-05/carrito-con-ofertas.png`
- `docs/evidence/RF-05/oferta-no-disponible.png`
- Resultado de las pruebas asociadas y puerta de calidad del incremento.

#### Fuera de alcance

- Suscripciones y planes periódicos.
- Cantidades superiores a uno.
- Carrito anónimo o fusión de carrito después del login.
- Cupones, impuestos, envío y múltiples monedas.
- Checkout, pedido e instantánea histórica, pertenecientes a RF-06.
- Pagos, licencias adquiridas y descarga.
- Gestión del carrito mediante API, perteneciente a RF-13.

#### Trazabilidad

RF-05 está `Aprobado`. D-CAT-01 define la venta unitaria sin suscripciones ni
stock; D-CAT-02 establece que la selección comprable es una oferta concreta de
producto y licencia; D-CAT-09 reserva la instantánea histórica para RF-06.
Las decisiones operativas aprobadas resuelven la prioridad entre método,
autenticación y CSRF, además del ciclo de vida de la selección actual. Todavía
no existen evidencias visuales del flujo. La puerta de calidad del 2026-09-18
acredita las comprobaciones automatizadas, pero RF-05 conserva el estado
`Aprobado` hasta completar la evidencia requerida y la dependencia de RF-13.

| Criterio | Prueba | Implementación | Estado |
|---|---|---|---|
| CA-RF05-01 | `apps/cart/tests/test_views.py` | `apps/cart/views.py`, `apps/cart/urls.py` y `config/urls.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-02 | `apps/cart/tests/test_views.py` | `apps/cart/views.py`, `apps/cart/selectors.py` y `apps/cart/templates/cart/cart_detail.html` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-03 | `apps/cart/tests/test_views.py` y `apps/cart/tests/test_services.py` | `apps/cart/services.py`, `apps/cart/views.py` y `apps/cart/urls.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-04 | `apps/cart/tests/test_models.py`, `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/models.py`, `apps/cart/services.py` y `apps/cart/views.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-05 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/models.py`, `apps/cart/services.py` y `apps/cart/templates/cart/cart_detail.html` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-06 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/catalog/selectors.py`, `apps/cart/services.py` y `apps/cart/views.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-07 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/selectors.py` y `apps/cart/templates/cart/cart_detail.html` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-08 | `apps/cart/tests/test_services.py` | `apps/cart/selectors.py` y `apps/cart/templates/cart/cart_detail.html` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-09 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/selectors.py` y `apps/cart/templates/cart/cart_detail.html` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-10 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/services.py`, `apps/cart/views.py` y `apps/cart/urls.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-11 | `apps/cart/tests/test_services.py` y `apps/cart/tests/test_views.py` | `apps/cart/services.py`, `apps/cart/selectors.py` y `apps/cart/views.py` | Implementado y comprobado; evidencia visual pendiente |
| CA-RF05-12 | `apps/cart/tests/test_services.py` | `apps/cart/services.py` | Servicio compartido implementado y comprobado; equivalencia API pendiente de RF-13 |

RF-05 conserva el estado `Aprobado`: CA-RF05-12 depende de RF-13 y faltan las
evidencias visuales previstas para declarar el requisito `Verificado`.

## RF-06: Convertir el carrito en un pedido histórico

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Cliente autenticado |
| Prioridad | Must |
| Versión objetivo | v0.4.0 |
| Estado | Implementado |
| Dependencias | RF-04, RF-05, D-CAT-09, RNF-01, RNF-03 a RNF-05, RNF-08, RNF-10 y RNF-11 |

RF-06 está implementado con modelos históricos, una migración inicial, un
servicio transaccional y la entrada web privada. Este estado no acredita aún
la verificación completa del requisito ni una puerta de calidad final.

#### Objetivo

Convertir el carrito privado actual de un cliente en un pedido histórico cuyas
líneas no dependan de valores posteriores del catálogo, y vaciar ese carrito
en la misma transacción.

#### Contrato web aprobado

| Operación | Ruta | Método | Resultado |
|---|---|---|---|
| Convertir carrito propio | `/orders/create/` | `POST` | Crea un pedido `pending_payment`, vacía el carrito y redirige a `/cart/` |

La conversión resuelve el carrito únicamente desde el cliente autenticado; no
recibe `cart_id`, `owner_id`, líneas, importes ni moneda desde el navegador.
Una respuesta correcta usa PRG hacia `/cart/` e informa que se creó el pedido.
RF-09 definirá la consulta y cualquier identificador público del pedido.

#### Precondiciones

- El cliente está autenticado mediante RF-04.
- Su carrito contiene al menos una línea.
- Todas sus ofertas siguen disponibles al iniciar la conversión protegida.
- PostgreSQL está disponible para ejecutar la transacción y los bloqueos.

#### Flujo principal

1. El cliente envía un `POST` para convertir su propio carrito.
2. El sistema bloquea el carrito y sus líneas, y vuelve a comprobar la
   disponibilidad de producto, categoría, oferta y tipo de licencia.
3. El sistema crea un pedido con estado inicial `pending_payment`.
4. Copia en cada línea histórica el SKU, nombre de producto, licencia, versión
   de términos, precio y moneda actuales.
5. Calcula y persiste el total decimal en EUR a partir de esas líneas.
6. El sistema elimina las líneas bloqueadas del carrito y confirma toda la
   transacción.
7. El cliente vuelve a `/cart/`, que queda como selección vacía.

#### Flujos alternativos y errores

- FA-01: un carrito vacío responde `409` y no crea pedido ni líneas.
- FA-02: si una o más ofertas dejan de estar disponibles, responde `409`, no
  crea un pedido parcial y conserva el carrito completo.
- FA-03: si falla la creación del pedido, de sus líneas o el vaciado, la
  transacción se revierte por completo y el error no expone detalles internos.
- FA-04: dos conversiones simultáneas del mismo carrito se serializan; solo una
  puede crear el pedido y la siguiente encuentra el carrito vacío.
- FE-01: un `GET` sobre la conversión responde `405` y no modifica datos.
- FE-02: un `POST` sin CSRF válido responde `403`; un visitante anónimo con
  CSRF válido se redirige al login con `next=/cart/`, sin crear datos.

#### Reglas de negocio

- RN-RF06-01: el pedido pertenece exclusivamente al propietario del carrito
  convertido; ningún identificador de otro carrito puede influir en la acción.
- RN-RF06-02: el pedido se crea con estado `pending_payment`; RF-06 no crea un
  pago, una licencia ni una autorización de descarga.
- RN-RF06-03: cada línea histórica conserva una instantánea de SKU, nombre de
  producto, licencia, versión de términos, precio y moneda, sin una clave
  foránea obligatoria a la oferta actual del catálogo.
- RN-RF06-04: el total y la moneda se calculan en el servidor desde las líneas
  históricas; durante el MVP la moneda es únicamente EUR y los importes usan
  `Decimal` con dos decimales.
- RN-RF06-05: un cambio posterior del catálogo no modifica las líneas ni el
  total históricos del pedido.
- RN-RF06-06: la creación del pedido, sus líneas y el vaciado del carrito son
  una única transacción de PostgreSQL.
- RN-RF06-07: las mutaciones del carrito y su conversión bloquean el mismo
  carrito antes de cambiar líneas, para que una concurrencia no cree pedidos
  duplicados ni pierda líneas.

#### Criterios de aceptación

- CA-RF06-01: dado un cliente autenticado con un carrito propio que contiene
  una o más ofertas disponibles, cuando se convierte el carrito, entonces se
  crea un pedido histórico `pending_payment` de ese cliente con una línea por
  cada línea del carrito, su total en EUR y el carrito queda vacío.
- CA-RF06-02: dado un pedido creado desde un carrito, cuando cambian después el
  SKU, nombre, licencia, versión de términos, precio o moneda de una oferta,
  entonces las líneas históricas del pedido conservan los valores capturados
  durante la conversión y el total histórico no cambia.
- CA-RF06-03: dado un cliente autenticado con un carrito vacío, cuando intenta
  convertirlo, entonces recibe `409` y no se crea ningún pedido ni línea.
- CA-RF06-04: dado un carrito con una o más ofertas que dejan de estar
  disponibles antes de la conversión, cuando el cliente intenta convertirlo,
  entonces recibe `409`, no se crea ningún pedido y el carrito no cambia.
- CA-RF06-05: dado un fallo durante la creación del pedido, sus líneas o el
  vaciado del carrito, cuando termina la operación, entonces no persiste un
  pedido ni líneas históricas parciales y las líneas originales del carrito se
  conservan.
- CA-RF06-06: dados dos clientes con carritos distintos, cuando uno convierte
  su carrito, entonces el pedido creado pertenece solo a ese cliente y el
  carrito del otro no cambia.
- CA-RF06-07: dado un visitante o un método HTTP no permitido, cuando intenta
  convertir un carrito, entonces un `GET` recibe `405`, un `POST` sin CSRF
  válido recibe `403` y un `POST` anónimo con CSRF válido se redirige al login
  sin crear datos.
- CA-RF06-08: dadas dos conversiones simultáneas del mismo carrito, cuando se
  completan ambas solicitudes, entonces existe un único pedido creado a partir
  de esas líneas y no se pierden ni duplican datos.

#### Pruebas previstas

- Pruebas de modelo de la persistencia histórica y de sus restricciones en
  PostgreSQL.
- Pruebas de servicio para conversión, instantánea, total, indisponibilidad,
  reversión, aislamiento y concurrencia.
- Pruebas HTTP para `POST`, PRG, carrito vacío, métodos, autenticación y CSRF.

#### Migración prevista

RF-06 requerirá una migración inicial generada por Django para la persistencia
de pedidos y líneas históricas. Debe revisarse el usuario activo, el fichero
generado y el plan de migración antes de aplicarse en PostgreSQL.

#### Fuera de alcance

- Pago, reintento de pago, licencia adquirida, descarga y consulta histórica de
  pedidos, que corresponden a RF-07 a RF-11.
- Identificador público, detalle o listado de pedidos, que pertenecen a RF-09.
- API privada de pedido, que pertenece a RF-14.
- Cupones, impuestos, envío, stock, suscripciones, cantidades editables y
  múltiples monedas.

#### Implementación y pruebas existentes

- `apps/orders/models.py` define `Order` y `OrderItem`. El pedido conserva
  propietario, estado `pending_payment`, total decimal y moneda EUR; cada línea
  persiste SKU, nombre de producto, licencia, versión de términos, precio y
  moneda sin clave foránea a la oferta actual.
- `apps/orders/services.py` implementa `create_order_from_cart(owner=...)` en
  una transacción PostgreSQL. Bloquea carrito y líneas, revalida la
  disponibilidad compartida del catálogo, crea la instantánea y vacía el
  carrito. Los errores de dominio `EmptyCart` y `OfferNotAvailable` impiden
  crear pedidos o modificar líneas.
- `POST /orders/create/` delega en el servicio para el cliente autenticado,
  devuelve PRG hacia `/cart/` con el mensaje `Pedido creado.` y responde `409`
  para carrito vacío o una oferta no disponible. `GET` devuelve `405`; CSRF
  inválido devuelve `403`; un visitante con CSRF válido se redirige al login
  con `next=/cart/`. El detalle del carrito con líneas muestra el formulario
  visible `Crear pedido` con CSRF, sin enviar datos del pedido controlables por
  el navegador.
- `apps/orders/migrations/0001_initial.py` crea las tablas `Order` y
  `OrderItem`; depende del modelo de usuario intercambiable y no altera tablas
  existentes de carrito o catálogo.
- Las pruebas de servicio cubren conversión correcta, instantánea histórica,
  carrito vacío, indisponibilidad, reversión ante un fallo de creación de
  líneas, aislamiento entre propietarios y concurrencia con dos transacciones
  PostgreSQL. Las pruebas HTTP cubren el flujo correcto, ambos conflictos,
  método, CSRF y autenticación. La última ejecución conjunta observada de
  `apps/orders/tests` finalizó con `11 passed`.
- La puerta de calidad ejecutada tras incorporar la entrada visible finalizó
  con `155 passed`; las comprobaciones de Django y migraciones, Ruff, formato,
  `pip check` y `git diff --check` no informaron incidencias.

No se han generado evidencias en `docs/evidence/RF-06/`. La ausencia de esas
evidencias impide declarar RF-06 como `Verificado`.

#### Trazabilidad

RF-06 pasó de `Aprobado` a `Implementado` el 2026-09-18. D-CAT-09 define la
instantánea histórica y RF-05 define el carrito actual que se vacía tras una
conversión correcta. `apps/orders/` posee el pedido histórico, su servicio
transaccional y la interfaz web; `apps/cart/` conserva únicamente la selección
actual y bloquea el mismo carrito antes de modificar sus líneas.

La API privada de pedidos permanece diferida a RF-14. RF-06 conserva el estado
`Implementado`, no `Verificado`: la cobertura automatizada y la puerta de
calidad están registradas, pero faltan evidencias reales del requisito.

### RF-07 — Simular un pago aprobado de forma independiente

#### Metadatos y alcance

- Actor: cliente autenticado. Prioridad: Must. Versión objetivo: v0.5.0.
- Estado: `Verificado` el 2026-10-02 mediante pruebas automatizadas y evidencias
  reproducibles. El cierre documental y su commit se autorizan en esta fecha.
- Dependencias: RF-04, RF-06 y RF-09; RNF-01 a RNF-05, RNF-08, RNF-10 a RNF-13.
- Objetivo: aprobar un pago simulado de un pedido existente, sin volver a crear
  el pedido ni consumir el carrito actual. No se utilizan tarjetas, pasarelas,
  credenciales financieras, cobros reales ni webhooks.

#### Contrato implementado

`POST /orders/{order_id}/payments/simulate/` recibe `result=approved` y una
`idempotency_key` UUID. Son los únicos campos de negocio admitidos; el
formulario también incluye `csrfmiddlewaretoken`, que valida Django. Aparece
en el detalle propio pendiente e indica claramente que es una simulación.
Generar la clave del formulario no escribe datos de negocio. RF-08 incorpora `result=failed` a la misma operación desde el 2026-10-03.

Éxito: 302 al detalle propio, mensaje de pago simulado aprobado y estado `paid`.
GET sobre la operación: 405. POST sin CSRF: 403. Anónimo con CSRF válido: 302 al
login con `next` al detalle propio solicitado. Pedido ajeno o inexistente: 404
uniforme, incluso si se envían campos extra. Tras comprobar la propiedad,
entrada ausente, inválida o campos manipulables no admitidos: 400.
Pedido ya pagado con otra clave: 409. RF-08 amplía el conflicto por reutilizar
una clave con otro resultado al admitir también el rechazo simulado.

El servidor obtiene propietario, importe y moneda del pedido histórico. Un
intento persistido registra pedido, clave, resultado, importe, moneda y fecha.
La clave se identifica dentro del pedido; reutilizarla con otro resultado se
rechaza. La transición `pending_payment → paid` y el intento aprobado forman
una transacción con bloqueo del pedido; existe como máximo una aprobación por
pedido, también ante concurrencia. Un replay autorizado de la misma clave y
resultado devuelve el éxito original sin crear datos adicionales, aunque el
pedido ya esté pagado. Primero se valida propiedad; conocer una clave no concede
acceso. Un fallo técnico no se registra como rechazo simulado.

RF-07 termina inicialmente con pago y estado. Al implementar RF-10, su servicio
se ampliará para emitir derechos en esa misma transacción. Ese enlace y la
regularización de pedidos pagados anteriores forman parte de RF-10; no se
crean licencias provisionales ni derechos al abrir una página.

#### Criterios de aceptación

- CA-RF07-01: dado un pedido propio pendiente, cuando su propietario abre el
  detalle, entonces ve el formulario de simulación con CSRF y clave; ese GET no
  cambia pedido, intentos, carrito ni derechos.
- CA-RF07-02: dado un visitante anónimo, cuando envía el POST con CSRF válido,
  entonces se redirige al login con `next` interno y no se registra ningún pago;
  un POST sin CSRF devuelve 403 y un GET sobre la acción devuelve 405.
- CA-RF07-03: dado un cliente autenticado, cuando intenta pagar un pedido ajeno
  o inexistente, entonces recibe el mismo 404 sin información privada ni cambios.
- CA-RF07-04: dado un pedido propio pendiente, cuando solicita una aprobación
  válida, entonces se guarda un único intento aprobado, el pedido pasa a `paid`
  y el detalle informa del resultado y mantiene sus líneas históricas.
- CA-RF07-05: dado un catálogo o carrito distinto al de la compra, cuando se
  aprueba el pago, entonces el importe y moneda proceden de `Order`; ni el
  carrito actual ni los valores de `OrderItem` se alteran. Enviar propietario,
  importe, moneda o estado como campos extra responde 400 sin cambios.
- CA-RF07-06: dada una petición ya aprobada, cuando se repite con su misma clave
  y resultado, entonces se conserva un solo intento aprobado y el mismo pedido
  pagado; con una clave nueva recibe 409 sin una segunda aprobación.
- CA-RF07-07: dadas dos aprobaciones simultáneas del mismo pedido, cuando ambas
  terminan, entonces solo existe una aprobación persistida; la misma clave se
  resuelve como replay y una clave diferente como conflicto. La prueba usa
  transacciones y conexiones PostgreSQL independientes.
- CA-RF07-08: dado un fallo interno entre el registro del intento y la
  actualización del pedido, cuando se aborta la operación, entonces no queda
  ningún cambio parcial ni se vacía o modifica el carrito.
- CA-RF07-09: dado un resultado o clave inválidos, cuando se envía la petición,
  entonces recibe 400 sin persistir intentos ni cambiar el pedido; la respuesta
  no contiene secretos, rutas privadas ni detalles internos.

#### Implementación y verificación

`Order.Status.PAID` y `PaymentAttempt` persisten el resultado de la simulación.
La migración `orders.0004_alter_order_status_paymentattempt` incorpora esos
cambios y se encuentra aplicada en el entorno local comprobado.
`approve_simulated_payment` filtra por propietario, bloquea el pedido y agrupa
intento y transición en una transacción. La vista y el formulario están en
`apps/orders/`; importe y moneda se obtienen exclusivamente del pedido.

La revisión detectó que los campos extra anticipaban un 400 sobre pedidos
ajenos o inexistentes. Se corrigió para comprobar primero la propiedad y se
amplió CA-RF07-03 a cinco campos extra, manteniendo el 400 sobre pedidos propios.
Antes de la corrección: 5 fallos y 5 éxitos en la selección correspondiente;
después: 10 éxitos. La ausencia de escrituras de intentos también se comprueba
al abrir el formulario y ante peticiones no autorizadas.

Verificación final: 28 casos de RF-07 y 200 pruebas totales superadas con
PostgreSQL. Se utilizan conexiones PostgreSQL independientes para concurrencia
y se provoca un fallo después de insertar el intento para comprobar rollback.
Django, migraciones, Ruff, formato, dependencias y diff pasan sus controles.
Las ejecuciones y la correspondencia de CA01–CA09 se conservan en las
[evidencias de RF-07](../evidence/RF-07/README.md).

La verificación acredita el contrato HTTP, HTML y datos mediante pruebas de
integración. No se afirma una revisión visual manual ni capturas de navegador.
Los derechos aún no existen y su emisión corresponde a RF-10; la API privada,
a RF-14. El rechazo y el reintento se verifican en RF-08 el 2026-10-03;
un resultado distinto de `approved` o `failed` devuelve 400 conforme a CA-RF07-09.

#### Trazabilidad

El cierre autorizado el 2026-10-02 registra RF-07 como `Verificado` para su
alcance inicial de pago y estado, con CA-RF07-01 a CA-RF07-09 comprobados.
La implementación existente, la corrección de acceso, las pruebas, la migración
y estas evidencias forman un único commit reproducible. Su identificador se
obtiene con `git log -1 -- docs/evidence/RF-07/README.md`. No se reconstruye un
ciclo RED-GREEN de la implementación inicial: solo se atribuye el RED observado
a la corrección de prioridad de propiedad.

### RF-08 — Simular un pago fallido y reintentarlo

#### Metadatos y contrato implementado

- Actor: cliente autenticado. Prioridad: Must. Versión: v0.5.0.
- Estado: `Verificado` el 2026-10-03 para el contrato HTTP, HTML y persistencia
  de rechazo y reintento simulados. Dependencias: RF-07 y sus RNF, RF-06 y RF-09.
- Misma ruta y servicio de RF-07; se admite `result=failed` además de `approved`.
- Un rechazo simulado es un resultado de negocio: guarda un intento `failed`,
  mantiene `Order.status=pending_payment` y redirige al detalle con un mensaje
  comprensible. No es un error 500 ni un nuevo estado del carrito.
- Reintentar exige una clave nueva. Repetir la misma clave y resultado devuelve
  el resultado original; usar la misma clave con otro resultado devuelve 409.
- El detalle muestra intentos propios con resultado y fecha, ordenados por fecha
  e ID descendentes, y permite reintentar solo mientras el pedido esté pendiente.
  No muestra claves técnicas de idempotencia ni datos de otro propietario.
- No hay cobros reales, devolución de dinero, cancelación ni procesamiento asíncrono.

#### Criterios de aceptación

- CA-RF08-01: dado un pedido propio pendiente, cuando se simula un rechazo,
  entonces se registra un intento fallido, el pedido permanece pendiente y el
  cliente ve un mensaje que permite distinguir rechazo de aprobación.
- CA-RF08-02: dado un rechazo, cuando termina la operación, entonces no cambia
  el carrito ni las líneas históricas y no se emiten derechos o descargas.
- CA-RF08-03: dado un intento rechazado, cuando se repite con la misma clave y
  resultado, entonces no se duplica; si se reutiliza esa clave para aprobar,
  recibe 409 y se conserva el resultado original.
- CA-RF08-04: dado un pedido pendiente con un intento fallido, cuando se
  reintenta con una clave nueva y resultado aprobado, entonces conserva el
  intento fallido, añade una sola aprobación y pasa a `paid` mediante RF-07.
- CA-RF08-05: dado un pedido con intentos previos, cuando el cliente lo consulta,
  entonces ve exclusivamente su historial ordenado de intentos; la consulta no
  crea un nuevo intento ni cambia resultados o estados.
- CA-RF08-06: dado un pedido pagado, cuando se intenta registrar un rechazo o
  nuevo pago con otra clave, entonces recibe 409 y el pedido sigue pagado. Un
  replay de clave existente conserva su resultado histórico sin revertir el pedido.
- CA-RF08-07: dado un anónimo, un POST sin CSRF o un pedido ajeno/inexistente,
  cuando se intenta rechazar o reintentar, entonces se mantienen las respuestas
  de seguridad de RF-07 y no se escribe ningún dato.
- CA-RF08-08: dadas peticiones concurrentes de rechazo y aprobación, cuando se
  procesan, entonces los bloqueos serializan las transiciones: nunca se revierte
  un pago aprobado ni aparece más de una aprobación; un error técnico revierte
  el intento parcial y no se convierte en rechazo simulado.

#### Implementación y verificación

`PaymentAttempt.Result.FAILED` amplía el campo existente mediante la migración
`orders.0005_alter_paymentattempt_result`, aplicada en el entorno comprobado.
`approve_simulated_payment` conserva la comprobación de propietario, la
transacción y el bloqueo del pedido; admite ambos resultados y solo actualiza
el estado a `paid` cuando el resultado es `approved`.

La vista devuelve 302 al detalle con `Pago simulado rechazado.` o
`Pago simulado aprobado.` según el intento devuelto. Un replay del rechazo tras
una aprobación posterior mantiene el pedido pagado. Una clave nueva sobre un
pedido pagado o una clave reutilizada con otro resultado devuelve 409.

El selector precarga únicamente los intentos del pedido propio con orden
`-created_at, -id`. La plantilla muestra resultado y fecha incluso tras el pago,
sin publicar claves de intentos anteriores. El formulario de aprobación genera
una clave nueva mientras el pedido está pendiente; el rechazo se verifica
mediante POST con `result=failed`. La interfaz actual conserva el botón de
aprobación y no incorpora un botón específico de rechazo.

La prueba del historial comprueba ambos resultados, fechas visibles, desempate
por ID, prioridad de fecha sobre ID y ausencia de cambios en pedidos e intentos
de ambos clientes. Como comprobación técnica complementaria de CA-RF08-05, el
número de consultas permanece constante con uno y diez intentos, dentro de un
presupuesto de cinco consultas para el detalle autenticado. El presupuesto
previo de cuatro consultas de RF-09 se amplía por la precarga fija del historial;
se conserva la igualdad al pasar de una a diez líneas.

Para CA-RF08-07, anónimo con CSRF válido obtiene 302 al login con `next` al
detalle; sin CSRF obtiene 403; autenticado con CSRF válido y pedido ajeno o
inexistente obtiene 404 uniforme. Se comprueban rechazo y reintento. El token
inválido del reintento es una variante técnica complementaria.

La concurrencia usa dos conexiones PostgreSQL y admite los dos órdenes válidos:
rechazo primero produce dos intentos y 302/302; aprobación primero produce una
sola aprobación y 409 para el rechazo. En ambos casos el pedido termina pagado.
La regresión de RF-07 cubre dos aprobaciones concurrentes y un fallo técnico
tras insertar el intento: se revierte la transacción y no se registra un rechazo
como sustituto del error. Una ejecución concurrente no garantiza recorrer ambos
órdenes; los flujos secuenciales de CA-RF08-04 y CA-RF08-06 completan esos casos.

Las pruebas y resultados reproducibles figuran en las
[evidencias de RF-08](../evidence/RF-08/README.md). La verificación es automatizada
sobre PostgreSQL; no acredita revisión visual manual ni pasarela real.
CA-RF08-02 verifica carrito e historia intactos; la ausencia actual de módulos
de derechos y descargas se declara como límite. Las comprobaciones de emisión
y entrega deberán ampliarse al implementar RF-10 y RF-11, sin inventar entidades.
La API privada queda en RF-14.

#### Trazabilidad

Álvaro solicita el cierre y commit el 2026-10-03 tras comunicar la regresión
Green. Esta revisión contrasta el código, completa la cobertura del historial
y vuelve a ejecutar las comprobaciones. La documentación aún conservaba el
estado `Propuesto`; se alinea con la implementación realizada criterio a criterio
y con la verificación autorizada. No se atribuye una fecha de cambio documental
a `Implementado` que no se hubiera registrado.

El commit reúne código, migración, pruebas y documentación de RF-08; se identifica
con `git log -1 -- docs/evidence/RF-08/README.md`. Los cambios previos de otros
requisitos y metodología permanecen fuera de ese commit.

### RF-09 — Consultar los pedidos propios

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Cliente autenticado |
| Prioridad | Must |
| Versión objetivo | v0.4.0 |
| Estado | Implementado |
| Dependencias | RF-04, RF-06, RNF-01, RNF-03 a RNF-05, RNF-08, RNF-10 y RNF-11 |

#### Objetivo

Permitir que un cliente autenticado consulte únicamente sus propios pedidos
históricos creados desde el carrito, incluyendo el estado del pedido, el total
y las líneas capturadas durante la conversión.

RF-09 no crea pedidos ni modifica su estado. Su función mínima para el MVP es
hacer visible el resultado de RF-06 y preparar la continuidad hacia pago,
licencias adquiridas y descarga autorizada.

#### Contrato web mínimo aprobado

| Operación | Ruta | Método | Resultado |
|---|---|---|---|
| Listar pedidos propios | `/orders/` | `GET` | Muestra los pedidos del cliente autenticado |
| Consultar detalle propio | `/orders/{order_id}/` | `GET` | Muestra un pedido propio y sus líneas históricas |

El identificador usado en la URL pertenece al pedido, no al carrito ni a una
línea. Durante el MVP puede utilizarse la clave primaria interna si la vista
mantiene aislamiento estricto por propietario; un identificador público estable
podrá evaluarse como mejora posterior.

#### Decisiones operativas aprobadas

- `Order` incorporará `created_at` mediante migración para registrar el momento
  de creación del pedido.
- El listado de pedidos propios se ordenará por `created_at` descendente y, en
  caso de empate, por identificador descendente.
- El detalle del pedido usará exclusivamente la instantánea histórica de
  `Order` y `OrderItem`; no consultará el catálogo vivo para reconstruir los
  datos de compra.
- Las reglas de propietario, orden y carga de líneas se concentrarán en una
  frontera de consulta reutilizable por la vista web y por la futura API privada
  de RF-14, sin implementar todavía dicha API.
- La interfaz autenticada ofrecerá una entrada visible de navegación hacia el
  listado de pedidos propios.

#### Precondiciones

- El cliente está autenticado mediante RF-04.
- Puede existir cero o más pedidos creados previamente mediante RF-06.
- Los pedidos ya contienen sus líneas históricas y no dependen del estado actual
  del catálogo para mostrarse.

#### Flujo principal

1. El cliente autenticado accede al listado de pedidos desde la navegación o
  mediante la URL directa.
2. El sistema consulta únicamente los pedidos cuyo propietario es el usuario de
   la sesión.
3. El sistema ordena los pedidos por `created_at` descendente y, en caso de
  empate, por identificador descendente.
4. La página muestra cada pedido con identificador, fecha de creación, estado,
  total y moneda.
5. El cliente abre el detalle de uno de sus pedidos.
6. El sistema muestra el estado, total, moneda y líneas históricas del pedido:
   producto, SKU, licencia, versión de términos, precio y moneda.

#### Flujos alternativos y errores

- FA-01: si el cliente no tiene pedidos, el listado responde 200 y muestra un
  estado vacío comprensible.
- FE-01: un visitante anónimo se redirige al login con un `next` interno y no
  obtiene datos de pedidos.
- FE-02: si un cliente intenta abrir un pedido inexistente o perteneciente a
  otro usuario, el sistema responde 404 sin revelar si el pedido existe.
- FE-03: los métodos de escritura sobre las rutas de consulta no modifican
  pedidos. Cualquier transición de estado queda fuera de RF-09.

#### Reglas de negocio

- RN-RF09-01: un cliente solo puede listar y consultar pedidos propios.
- RN-RF09-02: el listado y el detalle utilizan los datos históricos de `Order`
  y `OrderItem`, no los valores actuales del catálogo.
- RN-RF09-03: consultar pedidos no crea, modifica, paga, cancela ni elimina
  pedidos.
- RN-RF09-04: un pedido ajeno se trata como inexistente para evitar fugas de
  información.
- RN-RF09-05: los importes se muestran con `Decimal` y la moneda persistida en
  el pedido y sus líneas.
- RN-RF09-06: la consulta debe cargar las líneas del pedido sin provocar una
  consulta adicional innecesaria por cada línea.
- RN-RF09-07: consultar el listado o el detalle no tiene efectos laterales
  sobre pedidos, líneas, carrito, pagos, licencias o descargas autorizadas.

#### Criterios de aceptación mínimos

- CA-RF09-01: dado un visitante anónimo, cuando intenta consultar el listado o
  el detalle de pedidos, entonces se redirige al login con un `next` interno y
  no recibe datos privados.
- CA-RF09-02: dado un cliente autenticado sin pedidos, cuando abre el listado,
  entonces recibe 200 y ve un estado vacío comprensible.
- CA-RF09-03: dado un cliente autenticado con uno o más pedidos propios, cuando
  abre el listado, entonces ve únicamente sus pedidos con identificador, estado,
  total y moneda.
- CA-RF09-04: dados dos clientes con pedidos distintos, cuando uno consulta el
  listado, entonces no aparecen pedidos del otro cliente.
- CA-RF09-05: dado un cliente autenticado con un pedido propio, cuando abre su
  detalle, entonces ve el estado, total, moneda y las líneas históricas con
  producto, SKU, licencia, versión de términos, precio y moneda.
- CA-RF09-06: dado un cliente autenticado, cuando intenta abrir un pedido ajeno
  o inexistente, entonces recibe 404 y no se revela información del pedido.
- CA-RF09-07: dado un pedido histórico, cuando cambian después los datos del
  catálogo, entonces el detalle del pedido sigue mostrando los valores
  capturados en `OrderItem`.
- CA-RF09-08: dado un cliente autenticado con varios pedidos propios, cuando
  abre el listado, entonces los pedidos aparecen ordenados por `created_at`
  descendente y, en caso de empate, por identificador descendente.
- CA-RF09-09: dado un cliente autenticado con pedidos propios, cuando consulta
  el listado o el detalle de un pedido, entonces no se crea, modifica ni
  elimina ningún pedido, línea, carrito, pago, licencia o descarga autorizada.
- CA-RF09-10: dado un pedido propio con varias líneas, cuando se consulta su
  detalle, entonces el sistema carga el pedido y sus líneas con un número
  acotado de consultas, sin una consulta adicional por cada línea.
- CA-RF09-11: dado un cliente autenticado, cuando navega por la interfaz
  principal, entonces dispone de una entrada visible para acceder al listado de
  sus pedidos.

#### Pruebas previstas

- Acceso anónimo al listado y al detalle.
- Listado vacío para cliente autenticado sin pedidos.
- Listado con pedidos propios y exclusión de pedidos ajenos.
- Detalle de pedido propio con líneas históricas.
- 404 uniforme para pedido inexistente o ajeno.
- Comprobación de que el detalle no depende de cambios posteriores del
  catálogo.
- Orden estable por `created_at` descendente e identificador descendente.
- Ausencia de efectos laterales al consultar listado o detalle.
- Consulta eficiente del detalle con sus líneas.
- Entrada de navegación visible para usuarios autenticados.

#### Evidencias previstas

- `docs/evidence/RF-09/listado-pedidos-vacio.png`
- `docs/evidence/RF-09/listado-pedidos-propios.png`
- `docs/evidence/RF-09/detalle-pedido-historico.png`
- Resultado de las pruebas asociadas y puerta de calidad del incremento.

#### Fuera de alcance

- Crear pedidos, perteneciente a RF-06.
- Pagar, reintentar pagos o cambiar estados de pago, perteneciente a RF-07 y
  RF-08.
- Crear o consultar licencias adquiridas, perteneciente a RF-10.
- Descargar archivos autorizados, perteneciente a RF-11.
- API privada de pedidos, perteneciente a RF-14.
- Facturas, cancelaciones, devoluciones, comunicaciones por correo y
  exportaciones.

#### Trazabilidad

RF-09 queda `Implementado` el 2026-09-26. Las rutas web privadas reutilizan
los selectores por propietario preparados en `2817481`; el listado incluye
fecha y acceso al detalle, y la plantilla de detalle usa exclusivamente los
campos históricos de `Order` y `OrderItem`.

La trazabilidad individual de CA-RF09-01 a CA-RF09-11, incluidos los nombres
exactos de las pruebas, está en [las evidencias de RF-09](../evidence/RF-09/README.md).
La [puerta de calidad del incremento](../evidence/RF-09/quality-gate-2026-09-26.md)
registra los comandos y resultados reales. El commit de implementación es el
que incorpora esa evidencia; puede localizarse con `git log -- docs/evidence/RF-09/`.

| Elemento | Referencia |
|---|---|
| Rutas y vistas web | `apps/orders/urls.py`, `apps/orders/views.py` |
| Consulta compartida | `apps/orders/selectors.py` |
| Presentación y navegación | `apps/orders/templates/orders/order_list.html`, `apps/orders/templates/orders/order_detail.html`, `templates/base.html` |
| Pruebas web | `apps/orders/tests/test_views.py` |
| Preparación técnica previa | `apps/orders/models.py`, migraciones `0002` y `0003`, pruebas de modelos y selectores; commit `2817481` |

CA-RF09-09 compara todos los registros y campos de `Order`, `OrderItem`, `Cart`
y `CartItem` antes y después de cada GET. Pagos, licencias adquiridas y descargas
autorizadas todavía no tienen modelos: esa parte de la cobertura deberá ampliarse
cuando se implementen RF-07, RF-08, RF-10 y RF-11. `LicenseType` representa el
catálogo de licencias, no una licencia adquirida.

El estado no pasa a `Verificado`: quedan pendientes la comprobación visual
manual y las tres capturas previstas. La navegación se comprueba en el HTML;
la prueba no acredita por sí sola su presentación visual en el navegador.
No se implementan API privada, pagos, licencias adquiridas ni descargas.

### RF-10 — Registrar y consultar permisos de uso con condiciones trazables

#### Metadatos y alcance

- Actor: cliente autenticado. Prioridad: Must. Versión: v0.6.0.
- Estado: `Verificado` el 2026-10-14 para HTTP/HTML, servicios y persistencia
  comprobados con PostgreSQL. Dependencias: RF-06 a RF-09; RNF-01 a RNF-06,
  RNF-08 y RNF-10 a RNF-13.
- Una licencia adquirida representa el permiso de uso registrado para el
  cliente de una línea pagada; no es el modelo de catálogo `LicenseType` ni
  acredita una transmisión de propiedad intelectual sobre la grabación.
  Conserva propietario a través del pedido, identificador, línea, fecha de
  emisión y estado `active`.
- Los datos visibles proceden de la compra histórica: producto, SKU, tipo de
  licencia, versión y texto de condiciones, concedente y titular declarado de
  los derechos. Identificar una versión sin conservar su contenido no basta.

#### Objetivo y decisión de orientación

Por instrucción del usuario del 2026-10-04, RF-10 se orienta a registrar y
consultar permisos de uso con condiciones trazables. «Mis licencias» se conserva
como nombre de la sección web y `/licenses/` como ruta. La orientación queda
acordada; los contratos y criterios de implementación siguientes permanecen
propuestos y se trabajarán uno a uno.

El cliente debe poder responder «qué uso tengo permitido, sobre qué producto,
según qué condiciones y de qué compra procede». Las condiciones describen el
alcance de uso, usos permitidos, restricciones, duración, territorio, carácter
exclusivo o no exclusivo y atribución cuando corresponda. Identifican al
concedente y al titular declarado de los derechos, que pueden ser distintos;
no se atribuye automáticamente esa titularidad a Foleyra.

El MVP conserva un registro de adquisición mediante pago simulado; ese registro
no verifica por sí mismo la titularidad real del proveedor ni sustituye la
revisión de condiciones necesaria para una explotación comercial real.

#### Condiciones trazables: contrato propuesto

- Antes de crear el pedido, el cliente puede consultar las condiciones completas
  de la oferta y su versión desde la selección de compra. Un resumen de licencia
  no sustituye el texto completo.
- Las nuevas líneas de pedido capturan en el servidor la versión y el texto
  completo de las condiciones, el alcance de uso, el concedente y el titular
  declarado, además de los snapshots existentes. Estos datos se capturan al
  crear el pedido, no se reconstruyen desde el catálogo al pagar o consultar.
  El modelo concreto y los nombres de campos se definirán al abordar el criterio.
- El contenido capturado es histórico e inmutable. Una modificación de las
  condiciones publicadas exige una nueva versión para ese tipo de licencia;
  no sobrescribe las condiciones de pedidos existentes ni obliga al cliente
  a adquirir de nuevo la misma combinación de producto y tipo de licencia.
  La aprobación usa las condiciones capturadas por el pedido pendiente.
- Una nueva conversión sin condiciones completas o identidades declaradas
  responde 409 con mensaje comprensible, sin pedido parcial ni vaciado del
  carrito. Un pedido pendiente antiguo sin esa preparación tampoco puede
  aprobarse: responde 409 sin intento, cambio de estado ni emisión de permisos.
- Las compras anteriores que solo guardan `terms_version` siguen consultables.
  Se indica «Condiciones históricas pendientes de documentación» cuando falta
  el contenido, sin mostrar condiciones actuales como si fueran las compradas.
  Solo una operación explícita con correspondencia revisada puede completar
  esos datos; conserva los snapshots originales, es idempotente y no inventa
  condiciones ni reconstruye una aceptación del usuario que no esté registrada.
  La emisión de derechos para pedidos ya pagados prevista en CA-RF10-10 no
  convierte por sí sola esas condiciones desconocidas en condiciones trazables.
- El detalle de cada permiso muestra las condiciones capturadas y su procedencia
  de compra. El listado conserva una representación breve con versión; consultar
  el texto no genera ni modifica permisos.

#### Fuera de alcance de esta orientación

Generación de contratos o certificados PDF, firma electrónica, registro oficial
de propiedad intelectual, DRM, detección automática de copias y reclamaciones
automáticas. Tampoco se incorporan transferencias, suscripciones o revocaciones
desde la interfaz del cliente. Un aviso de copyright puede identificar al titular
declarado; no sustituye las condiciones ni se presenta como certificado de
titularidad. La entrega privada del archivo continúa en RF-11.

#### Contrato e integración verificados

`GET /licenses/` lista derechos propios por emisión e ID descendentes.
`GET /licenses/{license_id}/` muestra un derecho propio y referencia a su pedido.
Sin resultados: 200 con mensaje comprensible. Anónimo: login con `next` interno.
Ajeno/inexistente: 404 uniforme. Escrituras sobre estas consultas: 405.
La navegación autenticada incluye «Mis licencias».

La aprobación de RF-07 se amplía aquí: pago, estado `paid` y un derecho por cada
línea se confirman atómicamente. La unicidad por línea se protege en PostgreSQL;
repeticiones no duplican derechos. El GET nunca emite licencias. Para pedidos
`paid` creados antes de RF-10 se usa una operación administrativa explícita e
idempotente de regularización, probada aparte; no se ejecuta al consultar.

Preparación necesaria para RF-11: las nuevas líneas capturan una referencia
estable al producto de origen (`source_product`, nombre técnico propuesto),
protegida contra borrado, además de sus snapshots. No se resuelve el producto
por un SKU mutable. La relación admite nulo durante la transición para conservar las líneas
antiguas, sin inventar asociaciones. Nunca reconstruye los campos históricos
desde el catálogo. Las líneas antiguas mantienen sus datos; un mapeo técnico solo se completa con correspondencia explícita y revisada. Una
referencia desconocida permanece sin resolver y nunca habilita otra compra.
Esta ampliación del servicio de checkout y su migración forman parte del
incremento; no modifica importes, propiedad ni textos históricos de RF-06/09.

#### Regla de negocio: impedir la recompra de una licencia adquirida

- RN-RF10-01: un cliente con un derecho activo no puede comprar de nuevo la
  misma combinación de producto y tipo de licencia. La identidad se comprueba
  mediante referencias técnicas estables; no mediante nombres, SKU, precio,
  moneda o textos de términos que puedan cambiar en el catálogo. Un cambio de
  precio o de versión de términos no habilita por sí solo una nueva compra de
  esa misma combinación. Otro tipo de licencia o producto queda fuera de este
  bloqueo y sigue sujeto a las demás reglas de compra.
- Al implementar RF-10, los servicios de alta en carrito y creación de pedido
  rechazan la combinación ya adquirida con 409 y un mensaje comprensible,
  sin modificar el carrito ni crear otro pedido. La aprobación de pago vuelve
  a comprobarla: si se adquirió mediante otro pedido mientras este estaba
  pendiente, rechaza la nueva aprobación con 409, sin registrar un intento,
  cambiar el estado ni emitir derechos. No elimina automáticamente selecciones
  del carrito ni modifica pedidos históricos.
- Esta protección se comparte entre web y la futura API privada y debe cubrir
  dos pedidos distintos que intenten adquirir simultáneamente la misma
  combinación. La unicidad por línea no basta para impedir esa recompra.
  Repetir una aprobación ya confirmada con la misma clave conserva el éxito
  original según RF-07; ese replay no se considera una nueva compra.
- La preparación técnica de CA-RF10-11 se amplía con una referencia estable al
  tipo de licencia de origen (`source_license_type`, nombre propuesto), además
  de `source_product`. Las líneas antiguas requieren correspondencia explícita
  y revisada durante la regularización; una identidad sin resolver no permite
  afirmar que se ha comprobado la ausencia de una licencia previa. Resolver
  estos casos es condición de cierre de la regla, sin inventar asociaciones ni
  sobrescribir los snapshots históricos.

#### Criterios de aceptación verificados

- CA-RF10-01: dado un pago aprobado para un pedido con varias líneas, cuando se
  confirma la transición, entonces existe exactamente un derecho activo por
  línea y todos pertenecen al propietario del pedido; repetir la aprobación no
  duplica derechos.
- CA-RF10-02: dado un pedido pendiente o con intentos fallidos, cuando se
  consulta «Mis licencias», entonces no aparecen derechos para esas líneas.
- CA-RF10-03: dado un fallo al emitir una de las licencias, cuando se aborta la
  aprobación, entonces pago, pedido y derechos revierten juntos; una carrera de
  emisión nunca deja derechos duplicados o un pedido recién pagado sin ellos.
- CA-RF10-04: dado un cliente autenticado sin derechos, cuando abre el listado,
  entonces recibe 200 y un estado vacío, sin crear licencias al consultar.
- CA-RF10-05: dados dos clientes con derechos distintos, cuando uno abre su
  listado, entonces ve solo los suyos, con identificador, pedido, producto,
  licencia, versión de términos, fecha y estado, en el orden definido.
- CA-RF10-06: dado un permiso propio, cuando se abre su detalle, entonces
  muestra los datos históricos, las condiciones completas capturadas, su versión,
  alcance, concedente y titular declarado, y el enlace al pedido propio, sin
  sustituirlos por modificaciones del catálogo ni publicar rutas del maestro.
  Para una compra antigua sin condiciones documentadas muestra el aviso previsto,
  sin atribuirle condiciones actuales.
- CA-RF10-07: dado un anónimo o un identificador ajeno/inexistente, cuando se
  solicita listado o detalle, entonces se aplica login o 404 según el contrato;
  los métodos de escritura no modifican derechos.
- CA-RF10-08: dado un cliente autenticado, cuando navega por la interfaz
  principal, entonces encuentra «Mis licencias» y puede abrir un detalle propio.
- CA-RF10-09: dados uno y varios derechos propios, cuando se renderizan sus
  datos, entonces las consultas permanecen acotadas sin crecimiento por derecho,
  y listado/detalle no modifican pedidos, intentos, carrito ni derechos.
- CA-RF10-10: dados pedidos pagados anteriores sin derechos, cuando se ejecuta
  la regularización explícita, entonces se crean solo los faltantes para líneas
  pagadas; repetirla no duplica datos y no concede derechos a pedidos pendientes.
- CA-RF10-11: dada una nueva conversión de carrito, cuando se guarda la línea,
  entonces conserva la referencia técnica estable al producto y sus snapshots;
  cambiar el SKU después no rompe esa referencia. Las líneas antiguas sin mapeo
  continúan consultables y se identifican como pendientes de preparación de entrega.
- CA-RF10-12: dado un cliente con un derecho activo para un producto y tipo de
  licencia, cuando intenta añadir esa combinación al carrito, crear otro pedido
  que la contenga o aprobar otro pedido pendiente que la incluya, entonces se
  rechaza con 409 y un mensaje comprensible, sin nuevos pedidos, intentos o
  derechos ni cambios en los datos de negocio. Cambiar precio, moneda, nombre,
  SKU o versión de términos no elude el bloqueo; otro cliente sin ese derecho
  o una combinación distinta no se rechazan por esta regla. Dos aprobaciones
  concurrentes sobre pedidos diferentes no confirman dos adquisiciones de la
  misma combinación; el replay válido del pago original conserva su éxito.
- CA-RF10-13: dada una oferta preparada, cuando se crea un pedido, entonces
  cada línea captura la versión y texto completo de condiciones, alcance de uso,
  concedente y titular declarado desde el servidor junto con sus datos de compra;
  al aprobarse el pago su permiso consulta exactamente esos datos capturados.
- CA-RF10-14: dado un pedido pendiente o pagado con condiciones capturadas,
  cuando el catálogo publica otra versión, entonces su pago y consultas conservan
  las condiciones originales. Cambiar el contenido sin cambiar la versión del
  mismo tipo de licencia se rechaza sin sobrescribir datos históricos.
- CA-RF10-15: dada una compra antigua sin texto histórico, cuando se consulta,
  entonces muestra la ausencia de documentación sin usar términos actuales;
  completar una correspondencia explícita y revisada conserva los snapshots
  originales y repetir la operación no cambia datos. Una correspondencia ausente
  o ambigua se rechaza sin inventar condiciones ni constancia de aceptación.
- CA-RF10-16: dada una oferta con condiciones completas, cuando el cliente
  prepara la compra, entonces puede consultar su texto y versión antes de crear
  el pedido. Sin condiciones completas o identidades declaradas, la conversión
  responde 409 y conserva el carrito; un pedido pendiente sin esa preparación
  responde 409 al aprobar el pago, sin intento, cambio de estado ni permisos.

#### Orden y evidencias previstas

11: referencias técnicas de producto y tipo de licencia; 13–14 y 16: captura,
versionado y consulta previa de condiciones; 01–03: emisión transaccional;
10 y 15: datos anteriores y documentación histórica; 12: prevención de recompra
e integración con carrito, checkout y pagos; 04–08: consulta privada y navegación;
09: regresión y rendimiento.
Crear datos y consultar permisos son responsabilidades distintas aunque se
cierren en este requisito. Pruebas previstas de modelos, servicios y vistas;
evidencias en `docs/evidence/RF-10/`.

#### Avance parcial observado el 2026-10-11

En esa revisión el requisito conservaba `Propuesto` para los contratos
pendientes. Este apartado conserva la evidencia histórica; el cierre posterior
se registra a continuación. La evidencia del árbol publicado se recoge
en [RF-10](../evidence/RF-10/README.md).

- `LicenseGrant` existe y se emite por línea en la aprobación transaccional.
  Las pruebas cubren replay, fallo de emisión y aprobaciones concurrentes.
- `/licenses/` y su detalle están implementados con propiedad, login, métodos,
  navegación, orden y condiciones históricas. La lectura no crea permisos.
- Catálogo y líneas incorporan texto de condiciones e identidades declaradas;
  el checkout copia esos valores. Las compras antiguas incompletas muestran
  avisos sin reconstruir datos desde el catálogo.
- Las nuevas líneas capturan `source_product` con `PROTECT`, admitiendo nulo
  para las antiguas. No existe todavía `source_license_type`, un vínculo al
  maestro comprado ni una operación explícita de regularización.
- Continúan pendientes CA10, CA12 y CA16. CA14 tiene conservación de snapshots,
  pero falta rechazar cambios de contenido con la misma versión. CA15 dispone
  del aviso de datos antiguos, pero no de la regularización explícita.
  La referencia al tipo de licencia añadida al contrato de CA11 sigue pendiente.

Los tests de estas partes se identifican en la evidencia parcial. Una prueba
vacía con `pass` no acredita cobertura, aunque pytest la contabilice.

#### Cierre verificado del 2026-10-14

Por solicitud expresa del desarrollador, RF-10 pasa a `Verificado` para el
contrato web, servicios y persistencia del MVP. La matriz de los 16 criterios y
los límites están en [las evidencias de cierre](../evidence/RF-10/README.md);
los comandos reproducibles figuran en la
[puerta de calidad](../evidence/RF-10/quality-gate-2026-10-14.md).

El incremento incorpora `source_license_type` con PROTECT y nulo para datos
anteriores, reglas compartidas de documentación/recompra, bloqueo por propietario
en pagos concurrentes y validación del versionado de condiciones. Las consultas
conservan los snapshots y nunca regularizan datos automáticamente.

`regularize_paid_order_grants(order_ids=...)` crea solo permisos faltantes de
pedidos pagados. `regularize_legacy_order_item(order_item_id=..., mappings=...)`
exige una correspondencia única revisada, completa únicamente datos ausentes y
rechaza contradicciones. Son servicios internos para una operación administrativa
controlada; no hay un endpoint público ni una interfaz de regularización en Admin.
El revisor declarado no autentica al ejecutor ni representa aceptación del cliente.
Los metadatos de revisión se validan como entrada y aún no forman un registro de
auditoría persistente; su referencia documental debe conservarla el operador.

La verificación automatizada no acredita revisión visual, instalación limpia,
audios reales, despliegue, firma ni autenticidad jurídica del respaldo histórico.
Descargas, API privada y administración continúan en RF-11, RF-13/14 y RF-15.

### RF-11 — Descargar un archivo autorizado

#### Metadatos y alcance

- Actor: cliente autenticado con derecho adquirido. Prioridad: Must. Versión: v0.6.0.
- Estado: `Aprobado` por el desarrollador el 2026-10-16; implementación parcial
  revisada el 2026-10-22. Descarga y cierre de verificación pendientes.
  Dependencias: RF-06 a RF-10 y separación de maestros ya
  existente; RNF-01 a RNF-06, RNF-08 y RNF-10 a RNF-13.
- `GET /licenses/{license_id}/download/` entrega el archivo como adjunto mediante
  streaming, después de validar propietario, derecho activo, línea y pedido pagado.
- Una descarga autorizada es la decisión de acceso sobre un derecho persistido;
  no requiere crear un token, permiso nuevo o registro de descarga por cada GET.
  No se ofrecen enlaces públicos, firmados ni permanentes a almacenamiento en el MVP.
- Se permiten descargas repetidas del mismo archivo mientras exista el derecho.
  DRM, ZIP, conversión de audio, CDN y límites comerciales de descargas quedan fuera.
- Un pedido con varias líneas emite un derecho por línea y ofrece descargas
  individuales. Cada producto tiene un maestro; paquetes de varios archivos
  dentro de un producto y selección de formatos quedan fuera del MVP.
- El paso a `PAID` habilita el acceso; la descarga comienza cuando el cliente la
  solicita. El navegador se comunica con Django, nunca con PostgreSQL.

#### Reglas de negocio de calidad del maestro

- RN-RF11-01: todo maestro admitido debe tener una frecuencia de muestreo
  **igual o superior a 48000 Hz** y una profundidad de **al menos 24 bits por
  muestra**. Ambos mínimos son obligatorios, también para archivos asociados a
  compras antiguas; 44100 Hz o 16 bits no cumplen aunque el otro valor sea mayor.
- RN-RF11-02: se admiten WAV, incluido BWF con extensión `.wav`, y AIFF con
  audio PCM lineal sin compresión, y FLAC sin pérdida. BWF se representa como
  `audio_format=wav`; no introduce otra opción del catálogo. FLAC y AIFF están
  sujetos a los mismos mínimos que WAV.
- RN-RF11-03: la preparación valida el formato y las propiedades reales del
  archivo y su correspondencia con los metadatos del producto. No bastan la
  extensión, el tipo MIME declarado ni los valores introducidos en PostgreSQL.
  Un archivo ilegible, corrupto, de formato no admitido o inferior a los mínimos
  no se considera preparado. La validación debe corresponder al objeto privado
  que se captura y conserva para la compra, no al maestro actual del catálogo.
- RN-RF11-04: la entrega conserva los bytes completos, formato, resolución y
  metadatos embebidos del objeto comprado. No convierte FLAC/AIFF a WAV ni
  normaliza, limita, remuestrea o vuelve a codificar el audio durante el GET.
- RN-RF11-05: la preparación parte de material que cumple el mínimo; aumentar
  artificialmente frecuencia o profundidad de una fuente inferior no recupera
  información ni acredita esta regla. La inspección técnica automatizada no
  demuestra por sí sola la resolución de origen ni sustituye la revisión de
  procedencia y escucha del maestro real.

Foleyra adopta estos mínimos como regla de negocio obligatoria a partir de la
recomendación de IASA-TC 04 para grabaciones de campo (apartado 5.7.2.1: WAV/BWF,
al menos 48 kHz y grabación aconsejada a 24 bits). La admisión adicional de FLAC
y AIFF es una decisión de Foleyra; no se atribuye a IASA una recomendación de
esos formatos ni una certificación del producto. Esta revisión actualiza
[D-CAT-04](catalog-decision-checkpoint.md#d-cat-04--características-del-archivo-adquirido).

#### Identidad del archivo y política de entrega aprobadas

PostgreSQL conserva las referencias y datos de negocio; los bytes se guardan
en almacenamiento privado. El MVP utiliza el almacenamiento de disco ya
existente. Un despliegue puede usar un volumen persistente del servidor o un
almacenamiento de objetos privado con un adaptador compatible; RF-11 no exige
contratar nube ni implementa ahora esa migración. En cualquier despliegue se
deben conservar y respaldar tanto los archivos comprados como sus referencias,
sin publicar la raíz privada ni depender del disco del ordenador del autor.

Además de la referencia estable introducida en RF-10, la nueva línea de pedido
captura, durante el checkout, la clave interna del maestro preparado en el
almacenamiento privado. No se espera al pago para elegirlo. Esta clave
no se acepta desde el cliente, no es una URL y nunca se expone en HTML, JSON,
contextos de plantillas, errores ni logs. Las representaciones seleccionan los
campos permitidos y no incluyen objetos que expongan la clave. Reemplazar el maestro del catálogo produce otra clave y debe
conservar el objeto referenciado por compras anteriores. No se añade un gestor
de versiones: la aplicación y el Admin de RF-15 comparten una política que
escribe un objeto nuevo y no borra ni sobrescribe claves de compras anteriores.

«Maestro preparado» significa clave privada configurada, objeto existente,
calidad validada según RN-RF11-01 a RN-RF11-03 y asociación inequívoca con la
compra; no basta una cadena no vacía. La validación previa se vincula al objeto
conservado; no se exige decodificar de nuevo el audio en cada GET.

Al activar RF-11, el checkout debe rechazar con 409 una oferta cuyo maestro no
esté preparado para capturarse. El servicio de pago debe rechazar un pedido
pendiente sin maestro preparado con 409, sin crear una aprobación. Se comprueba
el objeto capturado por la línea, aunque el catálogo publique otro antes del pago.
Se amplían las pruebas y la documentación de RF-06/07 para estos dos guardas;
no se cambian los precios ni snapshots originales. Una pérdida operativa posterior
del archivo o una asociación cuya calidad no esté validada devuelve un error
controlado de descarga, nunca otro archivo ni una versión de menor calidad.

Para compras antiguas sin clave se exige una asociación explícita y revisada
con el archivo correcto. No se adivina por SKU, por nombre ni por el maestro
actual. Mientras falte esa asociación, la descarga devuelve 404 genérico y el
detalle propio informa de indisponibilidad. La regularización solo modifica el
vínculo técnico autorizado, conserva los datos históricos y es idempotente.

Anónimo: 302 al login con `next` interno. Licencia ajena, inexistente, inactiva,
pedido no pagado o maestro no preparado: 404 genérico sin información interna.
Métodos no admitidos: 405. Una respuesta exitosa es 200 con
`Content-Disposition: attachment`, nombre seguro derivado de datos históricos
públicos, extensión correspondiente al formato real del objeto comprado y
`Cache-Control: private, no-store`; no permite elegir rutas mediante parámetros.

#### Criterios de aceptación aprobados

- CA-RF11-01: dada una compra propia pagada y un derecho activo con archivo
  preparado, cuando se solicita la descarga, entonces recibe 200 y los bytes
  completos del maestro correcto como adjunto, con cabeceras privadas, nombre
  seguro y extensión de su formato, sin conversión ni alteración de metadatos.
- CA-RF11-02: dado un visitante anónimo, cuando solicita la descarga, entonces
  se redirige al login con `next` interno y no recibe bytes privados.
- CA-RF11-03: dado un identificador ajeno/inexistente, derecho inactivo o pedido
  no pagado, cuando se solicita la descarga, entonces recibe 404 sin bytes ni
  detalles que revelen la existencia de una compra ajena.
- CA-RF11-04: dado un maestro ausente, inválido o sin calidad validada, o una
  línea antigua sin asociación segura,
  cuando el propietario solicita la descarga, entonces recibe un error 404
  controlado; no se usa la preview ni un maestro de otro producto como alternativa.
- CA-RF11-05: dado el almacenamiento del maestro, cuando se inspeccionan rutas
  públicas, HTML, contextos, JSON y errores, entonces su clave, nombre interno y URL no son
  públicos; una ruta bajo `MEDIA_URL` no permite recuperar sus bytes.
- CA-RF11-06: dados cambios posteriores de SKU, nombre o maestro del catálogo,
  cuando se descarga una compra preparada, entonces se obtiene el archivo
  capturado para esa compra; desactivar el producto u oferta no revoca un derecho pagado.
- CA-RF11-07: dada una nueva compra sin maestro preparado, cuando se intenta
  convertir el carrito, entonces recibe 409 sin pedido parcial ni vaciado; un
  pedido pendiente sin maestro preparado recibe 409 al pagar, sin aprobación,
  cambio de estado ni derechos.
- CA-RF11-08: dada una compra antigua con correspondencia revisada, cuando se
  regulariza su vínculo de archivo, entonces queda asociada solo al maestro
  indicado y preparado conforme al mínimo de calidad, sin modificar propiedad,
  precios o términos; repetirlo no cambia
  el resultado y un mapeo inexistente o ambiguo se rechaza sin asociación.
- CA-RF11-09: dado un derecho válido, cuando se repite la descarga o se usa un
  método no admitido, entonces el GET autorizado mantiene los mismos derechos
  y datos de negocio y el método no admitido responde 405 sin escritura.
- CA-RF11-10: dado el detalle de una licencia propia preparada, cuando se abre,
  entonces ofrece un enlace de descarga autenticada; la autorización se vuelve
  a comprobar en el servidor aunque el cliente escriba la URL directamente.
- CA-RF11-11: dados maestros controlados WAV/BWF, FLAC y AIFF, cuando se valida
  su preparación, entonces se admiten los archivos válidos de al menos 48000 Hz
  y 24 bits, incluidos valores superiores compatibles. Se rechazan archivos por
  debajo de cualquiera de los mínimos, corruptos, de formato no admitido o con
  propiedades reales distintas de las declaradas, aunque su extensión y MIME
  aparenten ser correctos. El resultado se vincula al objeto conservado y lo
  reutilizan las guardas de checkout/pago y la regularización; no se modifica el
  archivo para hacerlo admisible.
- CA-RF11-12: dado un pedido propio pagado con varias líneas preparadas y un
  derecho activo por línea, cuando se accede a los permisos y se descarga cada
  uno, entonces cada enlace entrega únicamente los bytes del maestro de su
  línea; no mezcla archivos, no crea un ZIP y mantiene la autorización individual.

#### Orden y pruebas previstas

Orden aprobado, un criterio cada vez:

1. CA-RF11-05: revisar y reutilizar la protección de almacenamiento existente.
2. CA-RF11-11: validar formatos y mínimo técnico del objeto preparado.
3. CA-RF11-06: capturar el maestro histórico y conservarlo ante cambios.
4. CA-RF11-07: impedir checkout y pago sin ese maestro preparado, sin efectos parciales.
5. CA-RF11-08: regularizar asociaciones antiguas mediante correspondencia revisada.
6. CA-RF11-01: entregar los bytes correctos con nombre y cabeceras de descarga.
7. CA-RF11-02: redirigir al anónimo al login con retorno a la descarga.
8. CA-RF11-03: rechazar identificadores ajenos y derechos o pedidos no habilitados.
9. CA-RF11-04: controlar archivos ausentes, inválidos o sin asociación segura.
10. CA-RF11-09: admitir repetición sin escrituras y rechazar otros métodos.
11. CA-RF11-10: incorporar el enlace autenticado al detalle del permiso.
12. CA-RF11-12: verificar el recorrido con varios maestros en un pedido.

La autorización y el fallo seguro forman parte de la primera entrega de la
vista; los criterios 02–04 se verifican como incrementos separados sin dejar
una descarga privada públicamente accesible durante el desarrollo.
Se amplía CA-RF09-09 para los modelos de pago y derechos ya creados.
Las pruebas usan archivos de audio temporales válidos y controlados para cada
formato, además de casos inválidos. Se incluyen los límites 48000 Hz/24 bits,
44100 Hz/24 bits y 48000 Hz/16 bits, valores superiores y metadatos engañosos.
Se consume `streaming_content` para verificar los bytes exactos en los tres
formatos. No se leen ni copian maestros reales como fixtures. La procedencia y
escucha se comprueban después con una muestra real en la validación manual.
Evidencia incremental: [RF-11](../evidence/RF-11/README.md).

#### Avance parcial revisado el 2026-10-22

- El catálogo público representa campos permitidos y comprueba la privacidad
  del maestro en HTML, contextos, API y rutas directas de medios.
- `validate_master_audio` inspecciona propiedades reales y calcula tamaño y
  SHA-256. `prepare_master_audio` persiste evidencia idempotente y rechaza
  contenido o evidencia distintos bajo una clave ya preparada.
- `set_product_master_audio` guarda otra clave, prepara y asigna el maestro
  mediante transacción de datos, conservando los anteriores. No hay interfaz
  administrativa de carga conectada.
- El checkout captura `OrderItem.master_preparation`. La sustitución posterior
  del catálogo conserva vínculo, datos históricos y bytes originales en las
  pruebas específicas. Las migraciones no asignan archivos a compras antiguas.
- Checkout y nueva aprobación rechazan preparación ausente o archivo perdido
  mediante `MasterNotPrepared`, que sus vistas traducen a 409. El pago usa la
  preparación de la línea y conserva el tratamiento de intentos repetidos.
  Hay pruebas HTTP de ausencia de maestro y pérdida antes de checkout/pago.
- Faltan pruebas específicas del pago sin vínculo capturado y tras cambiar
  el maestro del catálogo. La prueba de línea sin vínculo está guardada como borrador
  incompleto y todavía no acredita ese comportamiento.
- Continúan pendientes la asociación revisada de compras antiguas, la ruta
  protegida, controles HTTP y de autorización, entrega exacta y cabeceras,
  enlace, varias líneas y recorrido manual con sonidos reales y dos cuentas.
  La prueba anónima conserva `xfail(strict=True)` y no acredita su criterio.

Este registro no cambia RF-11 a `Implementado` ni `Verificado`, ni cierra
los criterios que también requieren comprobar la descarga final.

#### Referencias oficiales revisadas el 2026-10-16

- [IASA-TC 04, 5.7.2: grabaciones de campo](https://www.iasa-web.org/tc04/field-recording-standards).
- [IASA-TC 04, principios digitales: frecuencia y profundidad, 2.2 y 2.3](https://www.iasa-web.org/tc04/key-digital-principles).
- [IASA-TC 04, edición española: formatos WAVE y BWF, 2.8](https://www.iasa-web.org/book/export/html/3489).
- [RFC 9639: FLAC, audio PCM con compresión sin pérdida](https://www.rfc-editor.org/rfc/rfc9639.html).
- [Apple, especificación original AIFF 1.3, copia en McGill: Common Chunk y Sample Points](https://www.mmsp.ece.mcgill.ca/Documents/AudioFormats/AIFF/Docs/AIFF-1.3.pdf).
- [Django 5.2: FileField y almacenamiento de referencias](https://docs.djangoproject.com/en/5.2/ref/models/fields/#filefield).
- [Django 5.2: FileResponse y entrega como adjunto](https://docs.djangoproject.com/en/5.2/ref/request-response/#fileresponse-objects).

### RF-12 — Consultar el catálogo mediante una API pública

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Consumidor de la API |
| Prioridad | Must |
| Versión objetivo | v0.2.0 |
| Estado | Verificado |
| Dependencias | RF-01, RF-02, RF-03, RNF-01, RNF-03 a RNF-07 y RNF-09 a RNF-11 |

#### Objetivo

Exponer una interfaz REST pública, de solo lectura y versionada para consultar
la misma selección de productos disponible en la web.

#### Contrato HTTP aprobado

| Operación | Ruta | Resultado |
|---|---|---|
| Listar | `GET /api/v1/catalog/products/` | Página de productos activos |
| Consultar detalle | `GET /api/v1/catalog/products/{slug}/` | Producto, preview y licencias |
| Metadatos HTTP | `HEAD` u `OPTIONS` sobre las rutas anteriores | Respuesta estándar DRF |

La lista acepta los parámetros válidos de RF-03: `q`, `category`, `license`,
`ordering` y `page`. La página tiene 12 elementos y usa la estructura `count`,
`next`, `previous` y `results`. `next` y `previous` son rutas relativas de la
API con los parámetros reconocidos de la consulta y el `page` correspondiente,
o `null` cuando no existe una página adyacente. Los parámetros desconocidos se
ignoran y no se incluyen en esos enlaces.

La implementación usará un `PageNumberPagination` local de `apps.catalog`.
No reutilizará directamente los enlaces construidos por el paginador estándar:
al generar `next` y `previous`, creará una consulta canónica con solo `q`,
`category`, `license` y `ordering` cuando tengan valor reconocido, en ese
orden, y añadirá o sustituirá `page` al final. El paginador no valida ni
normaliza parámetros; recibe de la vista únicamente valores ya validados. Así,
un parámetro ajeno como `utm_source` nunca aparece en una URL de respuesta.

Los campos de una tarjeta de lista son:

```json
{
  "name": "Nocturnos urbanos",
  "slug": "nocturnos-urbanos",
  "summary": "Ambiente ficticio de ciudad durante la noche.",
  "category": {"name": "Ambientes", "slug": "ambientes"},
  "duration_ms": 18500,
  "audio_format": "wav",
  "sample_rate_hz": 48000,
  "bit_depth": 24,
  "minimum_price": "12.90",
  "currency": "EUR",
  "licenses": [
    {
      "name": "YouTube y redes sociales",
      "slug": "youtube-redes-sociales",
      "usage_scope": "Un canal por plataforma",
      "summary": "Uso en contenido propio para redes sociales."
    }
  ],
  "detail_url": "/api/v1/catalog/products/nocturnos-urbanos/"
}
```

`audio_format` usa el valor técnico estable almacenado (`wav`, `flac` o
`aiff`), no una etiqueta localizada. Los importes `Decimal` se representan
como cadenas de dos decimales; la moneda es siempre `EUR` durante el MVP.
`licenses` contiene únicamente tipos de licencia con ofertas públicas y se
ordena como las ofertas públicas del producto: por precio y, ante empate, por
identificador.

El detalle contiene los mismos campos de la lista excepto `licenses`, añade
`description` y usa `license_offers` para representar cada oferta pública con
su precio:

```json
{
  "description": "Grabación preparada para una producción audiovisual.",
  "preview_url": "/media/previews/nocturnos-urbanos.mp3",
  "license_offers": [
    {
      "license": {
        "name": "YouTube y redes sociales",
        "slug": "youtube-redes-sociales",
        "usage_scope": "Un canal por plataforma",
        "summary": "Uso en contenido propio para redes sociales."
      },
      "price": "12.90",
      "currency": "EUR"
    }
  ]
}
```

`preview_url` es `null` cuando la preview no está disponible; nunca contiene
una URL, nombre o ruta del archivo maestro. `detail_url`, `next`, `previous` y
`preview_url` son rutas relativas; la preview solo puede pertenecer al
almacenamiento público configurado.

Los errores de API siempre devuelven JSON con este sobre:

```json
{"error": {"code": "invalid_query_parameter", "parameter": "ordering"}}
```

Los únicos códigos son `invalid_query_parameter` (400, con `parameter` igual a
`q`, `category`, `license` u `ordering`), `page_not_found` (404),
`product_not_found` (404) y `method_not_allowed` (405). Solo
`invalid_query_parameter` incluye `parameter`; los textos humanos no forman
parte del contrato.

La configuración global de DRF usa exclusivamente `JSONRenderer` y no define
autenticadores por defecto. Las vistas de RF-12 declararán explícitamente
`AllowAny` y `authentication_classes = []`; por tanto, una sesión existente o
la protección CSRF no pueden interceptar un método de escritura antes de que la
vista de solo lectura responda `method_not_allowed` con 405. Las futuras API
privadas deben declarar sus autenticadores y permisos en cada vista; no heredan
una política de acceso implícita.

#### Precondiciones

- La API v1 está disponible.
- El consumidor no necesita credenciales ni sesión.

#### Flujo principal

1. El consumidor realiza un `GET` sobre la lista o el detalle.
2. La API aplica explícitamente permiso público de solo lectura.
3. La API reutiliza la consulta pública y las reglas de disponibilidad de la
   interfaz web.
4. La API serializa exclusivamente los campos públicos definidos por RF-01 y
   RF-02.
5. La API devuelve JSON y códigos HTTP coherentes con el resultado.

#### Flujos alternativos y errores

- FA-01: una lista sin resultados responde 200 con `count` igual a cero y
  `results` vacío.
- FE-01: un producto inexistente o no disponible responde 404.
- FE-02: una página inexistente responde 404 con un error JSON.
- FE-03: un filtro conocido con valor inválido responde 400 con un error JSON.
- FE-04: un método de escritura responde 405.

#### Reglas de negocio

- RN-RF12-01: la API publica exactamente el mismo conjunto de productos que la
  web para una consulta equivalente.
- RN-RF12-02: el permiso público se declara de forma explícita; no depende del
  valor por defecto global de DRF.
- RN-RF12-03: ninguna representación contiene el archivo maestro, su nombre de
  almacenamiento, ruta, URL ni campos administrativos.
- RN-RF12-04: el endpoint es de solo lectura y no acepta creación, edición ni
  borrado.
- RN-RF12-05: la versión `v1` forma parte de la URL.
- RN-RF12-06: las relaciones necesarias se cargan de forma eficiente para
  evitar N+1 durante la serialización.

#### Representación pública mínima

La representación se limita a los campos definidos en el contrato HTTP
aprobado. No incorpora campos adicionales por comodidad del serializer.

#### Criterios de aceptación

- CA-RF12-01: dado un consumidor anónimo, cuando solicita la lista, entonces
  recibe 200 y una página JSON de productos disponibles.
- CA-RF12-02: dados los mismos filtros válidos, cuando se consultan web y API,
  entonces contienen el mismo conjunto de productos.
- CA-RF12-03: dado un `slug` disponible, cuando se solicita su detalle, entonces
  se devuelven metadatos técnicos, preview y ofertas activas.
- CA-RF12-04: dado un producto inactivo o inexistente, su detalle responde 404.
- CA-RF12-05: cualquier respuesta de lista o detalle omite el archivo maestro y
  los campos administrativos.
- CA-RF12-06: un intento de `POST`, `PUT`, `PATCH` o `DELETE` responde 405.
- CA-RF12-07: una página inexistente responde 404 y una consulta válida sin
  coincidencias responde 200 con una lista vacía.

#### Orden recomendado de implementación

Los identificadores anteriores permanecen estables; el orden siguiente evita
introducir una representación o una paginación antes de cerrar su frontera de
seguridad y su consulta compartida:

1. CA-RF12-01 y la parte de lista de CA-RF12-05: ruta, vista pública y
  serializer explícito de lista, con solo campos públicos.
2. CA-RF12-06: permitir exclusivamente lectura y comprobar 405 también con
  una sesión activa.
3. CA-RF12-07: paginación de 12, lista vacía y error JSON de página, incluidos
  enlaces canonizados que no reflejen parámetros desconocidos.
4. CA-RF12-02: validación HTTP de `q`, `category`, `license` y `ordering`, y
  equivalencia de `slug` con la web sobre el selector compartido.
5. CA-RF12-03 y la parte de detalle de CA-RF12-05: serializer y vista de
  detalle, preview pública opcional, ofertas activas y exclusión completa de
  datos privados.
6. CA-RF12-04: 404 JSON para `slug` inexistente y todas las combinaciones de
  indisponibilidad heredadas de RF-01 y RF-02.
7. Medición de RN-RF12-06: serializar una y doce filas, materializando
  categoría, licencias y ofertas para demostrar que no hay N+1.

#### Pruebas previstas

- Acceso anónimo explícitamente permitido.
- Lista, detalle, filtros, orden y paginación equivalentes a la web.
- Esquema exacto de tarjeta, detalle, paginación, enlaces relativos y códigos
  200, 400, 404 y 405, incluidos los sobres JSON de error.
- La configuración de DRF admite solo JSON y no tiene autenticadores por
  defecto; con una sesión activa, cada método de escritura de RF-12 sigue
  respondiendo 405 y el sobre `method_not_allowed`.
- Solicitud con `q`, `category`, `license`, `ordering`, `page` y un parámetro
  desconocido: los enlaces de página conservan solo los cuatro primeros con
  valores reconocidos, usan el número de página adyacente y permanecen rutas
  relativas.
- Exclusión de productos y ofertas no disponibles.
- Ausencia de campos y URLs privadas en toda respuesta.
- Número acotado de consultas durante la serialización.

#### Estado de verificación

RF-12 está `Verificado`. La API pública versionada expone exclusivamente
lectura en `/api/v1/catalog/products/` y
`/api/v1/catalog/products/{slug}/`, reutiliza el selector público de catálogo
y representa solo los campos definidos en este contrato.

Los criterios CA-RF12-01 a CA-RF12-07 están cubiertos por
`apps/catalog/tests/test_api.py`: lista anónima, equivalencia con la web para
los filtros y órdenes válidos, detalle y ofertas públicas, indisponibilidad,
privacidad del maestro, rechazo de escrituras y paginación. La medición de
RN-RF12-06 comprueba que serializar una y doce filas mantiene un número de
consultas constante y acotado; es una regresión Green preexistente, no un ciclo
RED-GREEN propio.

No se requirieron migraciones porque RF-12 no modifica modelos ni el esquema
de PostgreSQL. Permanecen fuera de alcance las API privadas y los requisitos
RF-04 a RF-11, incluida la descarga autorizada del archivo maestro.

La evidencia de la puerta de calidad, incluidas las respuestas manuales de
lista y detalle, se conserva en `docs/evidence/RF-12/` y corresponde al commit
`355cc2d`.

#### Evidencias previstas

- `docs/evidence/RF-12/api-catalogo-lista.json`
- `docs/evidence/RF-12/api-catalogo-detalle.json`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Autenticación por token, escritura, carrito, pedido, pago y descarga.
- Negociación de versiones distinta de la ruta `/api/v1/`.
- Documentación OpenAPI, limitación de tasa y caché HTTP, salvo requisito
  posterior aprobado.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | `apps/catalog/tests/test_api.py` |
| Selectores | `apps/catalog/selectors.py:get_available_products` |
| Serializers y vistas | `apps/catalog/serializers.py` y `apps/catalog/api_views.py` |
| Evidencia | `docs/evidence/RF-12/quality-gate-2026-09-02.md` |
| Commit | `355cc2d` |

### RF-13 — Gestionar el carrito mediante una API autenticada

#### Metadatos y autenticación propuestas

- Actor: cliente API autenticado. Prioridad: Must. Versión: v0.3.0 (etiqueta de
  alcance, no orden de ejecución). Estado: `Propuesto`.
- Dependencias: RF-04, RF-05 y RF-12; RNF-01 a RNF-06, RNF-08 y RNF-10 a RNF-13.
- Autenticación MVP: sesión Django de RF-04, `SessionAuthentication` e
  `IsAuthenticated` explícitos en cada vista privada. Escrituras con CSRF.
  No se añaden JWT, tokens, OAuth, emisión de credenciales ni login API.
- Un consumidor sin sesión válida recibe 403 JSON, no redirección al login;
  esta elección no promete 401. Sesión válida sin CSRF en escritura: 403 JSON.
- Se conserva RF-12 público, sin autenticación y con sus códigos propios.

#### Contrato HTTP propuesto

| Operación | Ruta y método | Resultado |
|---|---|---|
| Consultar carrito propio | `GET /api/v1/cart/` | 200 con resumen, incluso vacío; no crea carrito |
| Resolver ofertas comprables | `GET /api/v1/cart/offers/?product={slug}` | 200 con ofertas disponibles e IDs para un producto público disponible |
| Añadir oferta | `POST /api/v1/cart/items/` con `{"offer_id": 7}` | 201 si crea línea; 200 si ya estaba |
| Eliminar línea propia | `DELETE /api/v1/cart/items/{item_id}/` | 204 sin cuerpo |

La consulta autenticada de ofertas resuelve la obtención de `offer_id` sin
ampliar los campos de la API pública ni exigir acceso al Admin. Producto no
disponible/inexistente: 404; parámetro ausente/malformado: 400. Devuelve
`results` con `offer_id`, nombre y slug de licencia, precio y moneda, ordenados
por precio e ID. No modifica catálogo ni carrito.

El resumen tiene `items`, `total` y `currency`; cada línea contiene `item_id`,
`offer_id`, `product_name`, `product_slug`, `license_name`, `usage_scope`,
`terms_version`, `price`, `currency` e `is_available`. Se reutiliza
`get_cart_summary`; el alta devuelve la misma representación de línea.
Los importes JSON son strings de dos decimales con punto, moneda EUR y cantidad
implícita uno; las líneas se ordenan por ID ascendente, sin paginación del carrito.
La oferta no disponible permanece visible y se excluye del total comprable.

Errores: `{"error": {"code": "..."}}`, con catálogo cerrado para esta API:
403 `authentication_required` o `csrf_failed`; 400 `invalid_request`;
404 `product_not_found`, `offer_not_available` o `cart_item_not_found`;
405 `method_not_allowed`; 415 `unsupported_media_type` si existe un cuerpo
con tipo distinto de JSON. Se usa `JSONParser` para las escrituras con cuerpo;
DELETE sin cuerpo es válido. JSON malformado: 400 `invalid_request`. Una autenticación
fallida tiene prioridad sobre el método; las garantías de 405 se prueban con
sesión y CSRF válidos cuando corresponda. Los errores internos son genéricos,
sin trazas ni rutas privadas. Los códigos de RF-12 siguen siendo exclusivos de
sus endpoints, no un límite global para las nuevas API.

HEAD se permite en rutas GET con la misma autorización y cabeceras, sin cuerpo
ni escrituras; OPTIONS devuelve 200 con métodos permitidos solo tras autenticar,
sin datos de negocio. El resto de métodos fuera de contrato devuelve 405.
Esta regla se hereda en RF-14; no cambia los métodos de RF-12 ni de la web.

Campos extra de propietario, precio, moneda, cantidad o estado se rechazan con
400; el servidor obtiene identidad de la sesión. Un `offer_id` ausente, no entero,
booleano o no positivo se rechaza con 400; un entero positivo inexistente o
inactivo, con 404. El borrado ajeno y el inexistente producen el mismo 404.

#### Criterios de aceptación propuestos

- CA-RF13-01: dado un consumidor sin sesión válida, cuando accede a cualquier
  endpoint privado de carrito u ofertas, entonces recibe 403 JSON sin datos ni cambios.
- CA-RF13-02: dada una sesión válida, cuando se intenta escribir sin CSRF válido,
  entonces recibe 403 JSON sin cambios; con CSRF válido se evalúa la operación.
- CA-RF13-03: dado un usuario sin carrito o sin líneas, cuando consulta el resumen,
  entonces recibe 200 con `items=[]`, `total="0.00"` y `currency="EUR"`, sin crear datos.
- CA-RF13-04: dado un producto disponible, cuando el cliente consulta sus ofertas,
  entonces obtiene solo IDs y metadatos de ofertas comprables, que puede usar
  en el alta; un producto no disponible/inexistente devuelve 404 sin rutas privadas.
- CA-RF13-05: dada una oferta válida, cuando se añade, entonces se crea una línea
  propia con 201; repetir la misma oferta devuelve 200 y la misma línea, sin duplicarla.
- CA-RF13-06: dado un producto con dos ofertas de licencia distintas, cuando se
  añaden ambas, entonces permanecen dos líneas diferentes con cantidad implícita uno.
- CA-RF13-07: dada entrada malformada, JSON inválido o campos no admitidos, cuando
  se envía el alta, entonces recibe 400 sin cambios; una oferta inexistente o
  no disponible responde 404 y no crea carrito ni línea parcial.
- CA-RF13-08: dados dos clientes con carritos distintos, cuando uno consulta,
  entonces obtiene exclusivamente sus líneas, campos permitidos y total decimal
  calculado en el servidor, con el orden definido.
- CA-RF13-09: dada una línea propia, cuando se elimina con DELETE válido, entonces
  recibe 204 y cambia solo su carrito; una línea ajena o inexistente responde el
  mismo 404 y no modifica datos.
- CA-RF13-10: dado un cambio de precio o disponibilidad, cuando se consulta el
  carrito, entonces refleja los valores actuales y excluye del total las ofertas
  no disponibles, sin borrar líneas ni crear snapshots o pedidos.
- CA-RF13-11: dados datos y operaciones equivalentes por web y API, cuando se
  añade, repite, consulta o elimina una oferta, entonces coinciden líneas,
  disponibilidad, total y efectos de negocio mediante servicios/selectores
  compartidos; esto completa la equivalencia pendiente de CA-RF05-12.
- CA-RF13-12: dadas una y varias líneas, cuando se serializa el resumen, entonces
  no crece una consulta por línea; lecturas dejan intactos carrito, pedidos,
  intentos y derechos. Serializers y errores omiten maestros y campos internos.
- CA-RF13-13: dada una solicitud con sesión y CSRF válidos, cuando utiliza un
  método no contratado o cuerpo con tipo distinto de JSON, entonces recibe 405 o
  415 según el contrato y no hay cambios; HEAD y OPTIONS siguen las reglas auxiliares. La API pública mantiene su conducta previa.

#### Orden y reutilización

01–04: acceso, errores y lectura; 05–07: alta; 08–10: aislamiento y borrado;
11–13: equivalencia, regresión y eficiencia. La lógica de carrito ya existe en
`apps/cart/services.py` y `selectors.py`, pero no sus adaptadores privados DRF:
ningún criterio HTTP completo se etiqueta hoy como «solo pruebas».
Evidencia prevista: `docs/evidence/RF-13/`.

### RF-14 — Ejecutar checkout, pago y consultas privadas mediante API

#### Metadatos y alcance

- Actor: cliente API autenticado. Prioridad: Must. Versión: v0.7.0.
- Estado: `Propuesto`. Dependencias: RF-06 a RF-11 y RF-13; RNF-01 a RNF-06,
  RNF-08 y RNF-10 a RNF-13.
- Reutiliza autenticación por sesión, CSRF, JSON y errores de RF-13. No crea un
  segundo sistema de pagos, derechos o almacenamiento.
- Checkout significa convertir el carrito en pedido pendiente; pagar es otra
  petición. Repetir checkout con el carrito vacío responde 409, coherente con RF-06.

#### Contrato HTTP y representaciones propuestos

| Operación | Ruta y método | Resultado |
|---|---|---|
| Checkout | `POST /api/v1/orders/checkout/` con `{}` | 201 con detalle del nuevo pedido |
| Listado propio | `GET /api/v1/orders/` | 200 con `results`, vacío o pedidos propios |
| Detalle propio | `GET /api/v1/orders/{order_id}/` | 200 con pedido y líneas históricas |
| Pago simulado | `POST /api/v1/orders/{order_id}/payments/simulate/` | 201 nuevo intento; 200 replay de clave compatible |
| Licencias propias | `GET /api/v1/licenses/` | 200 con `results`, vacío o derechos propios |
| Detalle de licencia | `GET /api/v1/licenses/{license_id}/` | 200 con derecho propio |
| Descarga autorizada | `GET /api/v1/licenses/{license_id}/download/` | 200 streaming privado; errores JSON |

El pago recibe únicamente `result` (`approved`/`failed`) e `idempotency_key`.
Un rechazo simulado válido devuelve 201 con `result=failed`; no se confunde
con un error HTTP ni cambia el pedido a pagado. Un replay devuelve 200 con el
mismo intento, resultado, importe y fecha; `order_status` refleja el estado
actual del pedido. Repetir un fallo anterior después de aprobar conserva
`result=failed` y `order_status=paid`, sin revertir el pedido. Un fallo técnico revierte la transacción y no crea un intento
fallido artificial. La descarga exitosa es binaria, no JSON/base64; sus errores
respetan la política JSON privada y nunca redirigen al login.

Campos permitidos:

- Pedido de lista: `id`, `created_at`, `status`, `total_amount`, `currency`,
  `detail_url`. Orden por fecha e ID descendentes, como RF-09.
- Detalle: campos de lista y `items` con `id`, `product_name`, `product_sku`,
  `license_name`, `terms_version`, `price`, `currency`, ordenados por ID
  ascendente; `payment_attempts` con ID, resultado, importe, moneda y fecha,
  ordenados por fecha e ID descendentes. Sin claves de idempotencia o archivo.
- Resultado de pago: `attempt_id`, `order_id`, `result`, `order_status`,
  `amount`, `currency` y `created_at` del intento.
- Licencia: `id`, `order_id`, `order_item_id`, `status`, `issued_at`, nombre/SKU
  de producto, nombre de licencia y versión de términos históricos,
  `detail_url` y `download_url`. La URL de descarga apunta a la vista protegida,
  no al almacenamiento, y vale `null` cuando no hay entrega preparada.
  El detalle incorpora las condiciones completas históricas, alcance de uso,
  concedente, titular declarado y estado de documentación conforme a RF-10;
  sus nombres JSON se concretarán antes de implementar RF-14. Una ausencia
  histórica se representa explícitamente, sin sustituirla por términos actuales.

Los importes son strings decimales con punto; las fechas ISO 8601 incluyen zona
horaria. Las URL son relativas de la API. Las colecciones de pedidos y licencias
usan `results`, sin paginación en este MVP; las licencias siguen el orden de RF-10.
No se incluyen campos extra por comodidad del serializer ni referencias
internas de origen/almacenamiento. La cuenta se obtiene siempre de la sesión.

Errores comunes de RF-13 más: 404 `order_not_found`, `license_not_found`,
`download_not_found`; 409 `empty_cart`, `offer_not_available`,
`order_already_paid`, `idempotency_conflict`, `asset_unavailable`;
400 `invalid_request`. Checkout sin maestro preparado devuelve 409
`asset_unavailable`; aprobar un pedido sin maestro preparado usa ese mismo
409, sin intento aprobado, cambio de estado ni derechos. Propiedad se valida antes de informar del estado del pedido.
El archivo ausente o el derecho no válido usa el mismo 404 de descarga.
Errores técnicos: 500 genérico sin cambios parciales ni información interna.

#### Criterios de aceptación propuestos

- CA-RF14-01: dado un consumidor sin sesión válida o una escritura sin CSRF,
  cuando solicita estos endpoints, entonces recibe los 403 JSON definidos sin
  datos ni cambios; la descarga anónima tampoco devuelve bytes ni redirección.
- CA-RF14-02: dado un carrito propio válido y preparado para entrega, cuando se
  solicita checkout, entonces recibe 201 con un pedido pendiente y sus snapshots,
  se vacía únicamente su carrito y no se crea pago ni derecho todavía.
- CA-RF14-03: dado un carrito vacío, oferta no disponible o maestro no preparado,
  cuando se solicita checkout, entonces recibe el 409 correspondiente sin
  pedido parcial; un fallo interno revierte pedido, líneas y vaciado. Repetir
  tras un checkout exitoso con carrito vacío no duplica el pedido.
- CA-RF14-04: dados campos no admitidos de propietario, carrito, importes, estado
  o líneas, cuando se envían a checkout o pago, entonces recibe 400 y ningún
  valor manipulado gobierna los datos persistidos.
- CA-RF14-05: dado un cliente con cero o varios pedidos, cuando consulta el
  listado, entonces recibe 200, solo pedidos propios y el orden fecha/ID definido.
- CA-RF14-06: dado un pedido propio, cuando se consulta su detalle después de
  cambios del catálogo, entonces conserva sus valores históricos y solo su
  historial de intentos; pedido ajeno e inexistente reciben el mismo 404.
- CA-RF14-07: dado un pedido propio pendiente, cuando se aprueba un pago válido,
  entonces usa el importe histórico, pasa a pagado y emite un derecho por línea
  mediante la transición compartida de RF-07/10, sin cambiar el carrito actual;
  sin maestro preparado recibe 409 `asset_unavailable` sin aprobación, cambio
  de estado ni derechos.
- CA-RF14-08: dado un intento fallido o una solicitud repetida, cuando se paga o
  reintenta por API, entonces conserva historial, claves y estados según RF-07/08;
  el replay no duplica, un conflicto responde 409 y las carreras no producen
  dos aprobaciones ni derechos duplicados. Un pedido ajeno/inexistente responde 404.
- CA-RF14-09: dado un cliente autenticado, cuando consulta listado o detalle de
  licencias, entonces obtiene solo permisos propios y datos históricos; el detalle
  conserva las condiciones y el estado de documentación de RF-10. Ajeno e
  inexistente responden el mismo 404 y ningún GET emite derechos.
- CA-RF14-10: dado un derecho propio válido, cuando solicita descarga, entonces
  recibe los mismos bytes autorizados que por web y cabeceras privadas; las
  denegaciones usan JSON 404 y no exponen rutas o archivos alternativos.
- CA-RF14-11: dados resultados equivalentes por web y API, cuando se comparan
  checkout, pagos, reintentos, consulta y descarga, entonces coinciden las
  transiciones y datos de negocio; ambas interfaces reutilizan servicios y
  selectores, sin duplicar reglas en serializers.
- CA-RF14-12: dados uno y varios pedidos, líneas o derechos, cuando se serializan,
  entonces no aparece una consulta por cada relación; lecturas y descargas
  conservan registros y valores de pedidos, carrito, intentos y derechos.
- CA-RF14-13: dados todos los endpoints, cuando se inspeccionan respuestas de
  éxito/error y métodos no admitidos, entonces respetan campos y códigos del
  contrato, fechas, decimales y URL relativas, omiten maestros/secretos y
  responden 405 con autenticación y CSRF válidos cuando corresponda.

#### Orden y evidencias previstas

01 y 05–06: lectura privada; 02–04: checkout; 07–08: pagos; 09–10:
derechos y descarga; 11–13: equivalencia, rendimiento y contrato completo.
Los servicios RF-06/09 ya existen. Los de RF-07/08/10/11 deberán estar
implementados antes de esta fase. La API privada completa no existe todavía.
Evidencia prevista: `docs/evidence/RF-14/`.

### RF-15 — Administrar el sistema mediante Django Admin

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Administrador autorizado |
| Prioridad | Must |
| Versión objetivo | v0.9.0 |
| Estado | Aprobado |
| Dependencias | RF-01 a RF-14 según cada modelo, RNF-01, RNF-03, RNF-04, RNF-06 a RNF-08, RNF-10 y RNF-11 |

#### Objetivo

Permitir que personal autorizado mantenga el catálogo y consulte o gestione las
entidades operativas del MVP mediante Django Admin, sin convertir el Admin en
una vía para eludir reglas de negocio o permisos.

#### Precondiciones

- El usuario está autenticado, tiene `is_staff=True` y dispone de los permisos
  de modelo correspondientes.
- La entidad que se quiere administrar ya pertenece a un requisito aprobado e
  implementado.

#### Disparador

El administrador accede a `/admin/` y selecciona una entidad autorizada.

#### Flujo principal

1. Django Admin autentica al usuario y evalúa sus permisos.
2. El usuario visualiza únicamente los modelos para los que tiene permisos.
3. En el catálogo puede buscar, filtrar, ordenar y paginar categorías,
   productos, tipos de licencia y ofertas producto-licencia.
4. El usuario crea o modifica datos respetando las validaciones del dominio.
5. Los cambios de activación afectan a consultas públicas posteriores.
6. Django registra la modificación mediante su historial administrativo.

#### Flujos alternativos y errores

- FA-01: el operador retira un elemento mediante `is_active` en vez de borrar
  información con relevancia histórica.
- FE-01: un usuario anónimo o no perteneciente al personal no obtiene acceso al
  panel.
- FE-02: un usuario sin permiso de cambio puede consultar solo si posee permiso
  de visualización y no puede guardar modificaciones.
- FE-03: una operación que rompe una restricción o referencia protegida se
  rechaza con un error de validación comprensible.

#### Reglas de negocio

- RN-RF15-01: `is_staff` habilita el acceso al panel, pero las acciones dependen
  además de los permisos `view`, `add`, `change` y `delete` de cada modelo.
- RN-RF15-02: Django Admin coordina formularios administrativos; las reglas del
  dominio no existen únicamente en `ModelAdmin`.
- RN-RF15-03: productos, licencias, pedidos y autorizaciones con historia se
  retiran o cancelan mediante estado; no se borran de forma destructiva.
- RN-RF15-04: claves, contraseñas, secretos de pago y rutas internas no aparecen
  en listados, búsquedas, filtros ni mensajes.
- RN-RF15-05: los archivos maestros solo son accesibles para operaciones
  administrativas expresamente autorizadas y nunca mediante una URL pública.
- RN-RF15-06: las listas con relaciones deben evitar consultas N+1.
- RN-RF15-07: el Admin no concede una licencia ni confirma un pago saltándose el
  servicio de negocio aprobado para esas transiciones.

#### Criterios de aceptación

- CA-RF15-01: dado un usuario no autorizado, cuando intenta acceder al Admin,
  entonces no puede consultar ni modificar datos administrativos.
- CA-RF15-02: dado un administrador de catálogo con permisos, cuando crea o
  modifica categorías, productos, licencias y ofertas válidas, entonces los
  cambios se guardan.
- CA-RF15-03: cuando se desactiva un producto, categoría u oferta, entonces deja
  de aparecer en la web y API públicas.
- CA-RF15-04: los listados de catálogo ofrecen columnas útiles, búsqueda y
  filtros por estado y relaciones sin exponer campos privados.
- CA-RF15-05: dado un usuario `staff` sin permiso de cambio, cuando abre una
  entidad visible, entonces no puede modificarla.
- CA-RF15-06: dada una entidad protegida por historia de compra, cuando se
  intenta borrar, entonces la operación se rechaza o no se ofrece.
- CA-RF15-07: el historial administrativo permite identificar usuario, fecha,
  objeto y tipo de cambio realizado mediante Django Admin.

#### Datos y permisos

La matriz concreta de permisos por rol se aprobará antes de v0.9.0. Como mínimo
se separarán:

- administración de catálogo;
- soporte de pedidos y pagos en modo consulta u operación controlada;
- administración de usuarios, reservada a personal expresamente autorizado.

El acceso al archivo maestro, si se ofrece desde el Admin, requiere una vista
protegida; mostrar el valor de un campo de archivo no autoriza a publicar su
directorio de almacenamiento.

#### Delimitación y ampliación propuestas el 2026-09-27

Los CA-RF15-01 a CA-RF15-07 anteriores se conservan sin renumerar ni modificar:
su estado es `Aprobado`. Los contratos adicionales de esta sección y
CA-RF15-08 a CA-RF15-12 quedan `Propuesto`; no se consideran aprobados por
redactarlos. La matriz concreta anterior se propone ahora así:

| Perfil | Acceso y operaciones permitidas |
|---|---|
| Anónimo / cliente no staff | Sin acceso a datos administrativos |
| Staff sin permisos | Puede identificarse en Admin, pero no ver ni modificar modelos sin permiso |
| Gestor de catálogo | Permisos explícitos de ver, añadir y cambiar categorías, productos, tipos de licencia y ofertas; sin usuarios, pagos ni derechos; retirada por `is_active` |
| Soporte | Ver pedidos, líneas, intentos y licencias adquiridas; sin añadir, modificar, borrar, pagar ni conceder derechos desde formularios genéricos |
| Administrador de usuarios | Gestión explícita de cuentas y roles; separada de soporte y catálogo |

Las entidades históricas se presentan solo en lectura en el Admin, incluso si
un usuario tiene permisos de cambio genéricos. Se elimina el borrado individual
y masivo de estas entidades y del catálogo en este MVP; se desactiva catálogo.
No se añaden acciones administrativas para pagar, cancelar, revocar o emitir
licencias. Las regularizaciones técnicas de RF-10/11 utilizan operaciones
explícitas y servicios probados, no edición libre de claves o estados.
Las condiciones de licencia publicadas respetan el versionado de RF-10:
editar el catálogo no sobrescribe condiciones históricas de compra y cambiar
su contenido exige una nueva versión. La configuración administrativa concreta
se definirá al implementar esos criterios, sin edición libre de snapshots.

El campo maestro requiere un control de subida que no intente construir su
`.url()` privada. Muestra únicamente si hay archivo configurado, sin ruta,
nombre interno ni enlace al almacenamiento; el reemplazo respeta la conservación
de archivos referenciados por compras de RF-11. No se incluye una descarga
administrativa de maestros en el MVP. El nombre local elegido por el gestor
para subir un archivo no es la clave privada persistida. Contraseñas en claro, claves de
idempotencia y detalles internos no figuran en listados, búsquedas ni errores.

#### Criterios de aceptación adicionales propuestos

- CA-RF15-08: dados perfiles de catálogo, soporte y gestión de usuarios, cuando
  acceden al Admin, entonces cada uno puede ejercer solo las operaciones de la
  matriz; ser staff no concede permisos generales y las URL directas tampoco.
- CA-RF15-09: dados pedidos, líneas, intentos y licencias adquiridas, cuando
  soporte o un administrador abre sus pantallas, entonces solo puede consultar;
  una petición manipulada de alta, cambio o borrado no modifica estados,
  importes, propiedad, snapshots ni derechos y no ejecuta pagos.
- CA-RF15-10: dado un producto con maestro, cuando un gestor autorizado abre o
  guarda el formulario, entonces puede configurar el archivo mediante un control
  seguro sin generar una URL pública ni revelar la clave persistida o ruta interna; los cambios conservan
  el archivo asociado a compras anteriores y la retirada usa desactivación.
- CA-RF15-11: dados uno y varios objetos con relaciones en un listado
  administrativo, cuando se renderizan las columnas relacionadas, entonces las
  consultas permanecen acotadas, sin una consulta adicional por cada fila.
- CA-RF15-12: dados valores inválidos o una operación que vulnera una relación
  protegida, cuando se guarda desde Admin, entonces se informa del error sin
  cambios parciales, secretos ni trazas, y no se eluden restricciones del dominio.

#### Orden de implementación y código candidato existente

1. CA01: comprobar primero autenticación y permisos nativos de Django Admin.
2. CA02, CA04 y CA08: registrar modelos y configurar catálogo y matriz de roles.
3. CA03 y CA05: comprobar desactivación y lectura sin permiso de cambio.
4. CA06, CA09 y CA10: protección del histórico, prohibición de escrituras
   genéricas y almacenamiento privado.
5. CA07: verificar el `LogEntry` nativo para cambios válidos, con actor, fecha,
   objeto y acción; no darlo por verificado solo por usar Django Admin.
6. CA11 y CA12: consultas, validaciones y cierre de regresión.

`apps/users/admin.py` ya registra `UserAdmin`; `apps/catalog/admin.py` y
`apps/orders/admin.py` están vacíos. CA01 es candidato a pasar con una prueba
sobre la infraestructura existente. CA05 y CA07 pueden pasar con funciones
nativas después del registro de modelos. CA03 reutiliza selectores probados,
pero hoy falta la modificación desde Admin. CA06 no se da por resuelto por
`PROTECT`: los snapshots actuales no protegen por sí solos la historia comercial.

#### Pruebas previstas

- Acceso anónimo, usuario autenticado no `staff`, `staff` sin permiso y usuario
  con permisos concretos.
- Alta, modificación y desactivación de entidades del catálogo.
- Validaciones y referencias protegidas.
- Búsqueda, filtros, columnas y carga eficiente de relaciones.
- Efecto de la desactivación sobre web y API.
- Ausencia de secretos, rutas y enlaces públicos a archivos maestros.
- Uso de servicios para cambios de estado de pedido, pago, licencia y descarga.

#### Evidencias previstas

- `docs/evidence/RF-15/admin-catalogo.png`
- `docs/evidence/RF-15/admin-permisos.png`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Crear un backoffice a medida.
- Analítica avanzada, CMS, importaciones masivas y edición de audio.
- Conceder acceso administrativo general a cualquier usuario `staff`.
- Sustituir las interfaces privadas del cliente por Django Admin.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | Pendiente hasta la fase correspondiente |
| Configuración `ModelAdmin` | Pendiente |
| Reglas compartidas | Pendientes según RF-01 a RF-14 |
| Matriz de permisos | Pendiente de aprobación |
| Evidencia | Pendiente |
| Commit | Pendiente |


### RF-16 — Explorar el catálogo por familias y subfamilias sonoras

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Should |
| Versión objetivo | Evolución; por asignar |
| Estado | Propuesto |
| Dependencias | RF-01, RF-02, RF-03, RF-12; coherencia histórica con RF-06 y RF-10 |

#### Objetivo y límites

Permitir encontrar sonidos mediante dos niveles de clasificación comprensibles.
Una familia agrupa sonidos y una subfamilia concreta ese grupo. Por ejemplo:
Impactos → Distortion Wave → Distortion Wave 01. Los nombres y agrupaciones de
MotionPulse son referencias de preparación; no se copian automáticamente todas
sus carpetas ni se asume que una estructura de disco define el catálogo final.

Cada producto pertenece a una familia y, opcionalmente, a una subfamilia de esa
familia. Una subfamilia pertenece a una sola familia. No se contemplan niveles
adicionales, ciclos ni varias familias por producto en este incremento.
La familia describe el sonido; el tipo de licencia define condiciones de uso;
la oferta relaciona producto, licencia y precio. Se mantiene esa separación.

#### Comportamiento propuesto

- La interfaz permite elegir familia y, dentro de ella, subfamilia; ofrece una
  opción para consultar todas las subfamilias de la familia seleccionada.
- La búsqueda por nombre, resumen y descripción se combina con familia,
  subfamilia y licencia. Nombre y precio siguen siendo opciones de ordenación.
- Se conservan las reglas vigentes de precio mínimo global, disponibilidad,
  paginación estable y ausencia de datos privados.
- Una familia inactiva excluye sus productos y subfamilias del catálogo público;
  una subfamilia inactiva excluye sus productos. Una combinación de filtros
  conocida inválida responde 400; una combinación válida sin resultados, 200.
- La preparación inicial utiliza una muestra revisada de varias familias,
  productos y ofertas. Su nombre y metadatos describen el original seleccionado;
  la preview es un archivo separado. Los precios son datos de demostración,
  asociados a cada oferta, sin atribuirles una valoración comercial real.

#### Criterios de aceptación propuestos

- CA-RF16-01: dados productos de dos familias y dos subfamilias de una familia,
  al seleccionar esa familia aparecen sus productos disponibles; al elegir una
  subfamilia solo aparecen los pertenecientes a ella. Un producto asignado
  directamente a la familia aparece al consultar toda la familia.
- CA-RF16-02: una subfamilia de otra familia o un identificador inexistente o
  inactivo responde 400. Una consulta válida sin coincidencias responde 200
  y conserva visibles los controles y la selección.
- CA-RF16-03: búsqueda, clasificación y licencia se combinan sin recuperar
  productos no disponibles. Al ordenar y paginar se conservan los filtros y
  el desempate estable, con el precio mínimo global previsto en RF-03.
- CA-RF16-04: el listado muestra controles etiquetados «Buscar sonido»,
  «Familia sonora», «Subfamilia», «Tipo de licencia» y «Ordenar por». El detalle
  permite reconocer la clasificación del producto y volver al catálogo.
- CA-RF16-05: web y API obtienen el mismo conjunto de productos disponibles
  mediante consultas compartidas, con relaciones cargadas de forma acotada.
  El contrato vigente de RF-03/RF-12 conserva compatibilidad o requiere una
  evolución explícitamente documentada antes de sustituirse.
- CA-RF16-06: reclasificar o renombrar un producto no modifica los datos
  históricos de pedidos ni condiciones o permisos emitidos. Los productos
  existentes conservan una clasificación válida tras la adaptación del modelo.

#### Preparación técnica y comprobación

Antes de implementar, concretar cómo representar los dos niveles a partir de
`Category`, revisar datos existentes y definir la compatibilidad de parámetros
y respuestas de RF-03/RF-12. La migración se genera, revisa y autoriza en ese
paso; este texto no autoriza su aplicación. No hace falta una dependencia nueva
por el mero hecho de incorporar dos niveles.

Reutilizar y ampliar pruebas de selectores, vistas y API de catálogo. Añadir
solo escenarios que distingan familia de subfamilia y protejan las garantías
nuevas. La muestra manual debe permitir ver una exclusión real al filtrar.
Las pruebas automáticas crean sus datos y no dependen de la biblioteca personal.

No se incluyen importación de toda la colección, clasificador automático,
búsqueda semántica, favoritos, suscripciones ni formas de onda interactivas.
Las tarjetas visuales por familia pueden añadirse después de comprobar los
filtros; usarán recursos propios y la misma consulta de catálogo.

Pruebas, migración, capturas y commit de esta ampliación: pendientes.

### RF-17 — Completar el recorrido web mediante navegación visible

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Must para el recorrido manual |
| Versión objetivo | Evolución; por asignar |
| Estado | Propuesto |
| Dependencias | RF-01, RF-02, RF-04 a RF-10 |

#### Objetivo

Permitir completar el recorrido de compra y consulta mediante enlaces y
acciones visibles, sin recordar rutas ni escribirlas en la barra del navegador.
Se reutilizan las operaciones existentes y sus controles de autorización.

#### Criterios de aceptación propuestos

- CA-RF17-01: Inicio permite entrar en Catálogo; un visitante puede abrir un
  producto, escuchar su preview y volver. Un cliente autenticado dispone de
  accesos visibles a Inicio, Catálogo, Carrito, Mis pedidos y Mis licencias en
  las páginas de ese recorrido, incluidos los detalles de permisos.
- CA-RF17-02: después de añadir una oferta, el cliente puede revisar Carrito y
  seguir comprando mediante una acción visible que vuelve al catálogo. Esa
  acción también existe con el carrito vacío y permite preparar una compra
  de dos ofertas sin perder la selección anterior.
- CA-RF17-03: tras crear un pedido, una confirmación visible permite localizar
  el pedido recién creado y abrirlo. Desde Mis pedidos se abre su detalle y
  se puede aprobar el pago simulado. Tras pagarlo, se puede abrir Mis licencias,
  consultar un permiso emitido y volver al pedido del que procede.
- CA-RF17-04: los enlaces de consulta utilizan GET y no crean ni alteran
  registros. Añadir, eliminar, crear pedido y simular pago conservan POST,
  CSRF, autenticación, propiedad e idempotencia según su contrato existente.
  La navegación no permite acceder a compras o permisos ajenos.

#### Comprobación y evidencia

Recorrer con una cuenta de prueba los seis pasos: Inicio → Catálogo → producto
con oferta → Carrito con dos ofertas → pedido y pago → permiso y pedido de
origen. Revisar primero la cobertura existente; ampliar donde falte una
transición observable o una garantía de autorización.

Los cambios locales de acceso al catálogo, enlaces de producto y reproductores
son avances parciales, no el cierre de RF-17. Las capturas de este recorrido
pueden referenciarse desde las evidencias de RF-07 a RF-10, indicando qué
comportamiento acredita cada una. Los cambios de presentación no invalidan
resultados históricos, pero una captura nueva debe identificar su versión y
cambios locales relevantes.

El cierre de RF-17 no exige entregar maestros ni implementar RF-11. Un diseño
visual completo y la navegación jerárquica del catálogo se desarrollan por
separado. Pruebas específicas, capturas del recorrido completo y cierre:
pendientes.
