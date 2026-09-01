# Requisitos funcionales de Foleyra

## 1. Propósito

Este documento define las capacidades funcionales incluidas en el MVP
de Foleyra. Constituye la fuente de verdad para la planificación,
las pruebas, la implementación y las evidencias académicas.

## 2. Convenciones

- Los requisitos utilizan identificadores estables `RF-XX`.
- Un requisito no se implementa sin criterios de aceptación aprobados.
- Los estados posibles son: Propuesto, Aprobado, Implementado y Verificado.
- Las evidencias reales se incorporan después de implementar el requisito.
- Web y API deben reutilizar las mismas reglas de negocio.

## 3. Índice de requisitos

> Los requisitos incluidos en este índice forman parte del alcance previsto
> del MVP. Su presencia no implica que estén implementados. El estado de cada
> requisito indica su grado real de definición, desarrollo y verificación.

| ID | Título | Actor principal | Prioridad | Versión | Estado |
|---|---|---|---|---|---|
| RF-01 | Consultar el catálogo | Visitante o cliente | Must | v0.2.0 | Aprobado |
| RF-02 | Consultar el detalle y escuchar una preview pública | Visitante o cliente | Must | v0.2.0 | Aprobado |
| RF-03 | Buscar, filtrar, ordenar y paginar el catálogo | Visitante o cliente | Should | v0.2.0 | Implementado |
| RF-04 | Registrarse, iniciar sesión y cerrar sesión | Visitante o cliente | Must | v0.3.0 | Propuesto |
| RF-05 | Gestionar los productos del carrito privado | Cliente autenticado | Must | v0.3.0 | Propuesto |
| RF-06 | Convertir el carrito en un pedido histórico | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-07 | Simular un pago aprobado de forma independiente | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-08 | Simular un pago fallido y reintentarlo | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-09 | Consultar los pedidos propios | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-10 | Consultar las licencias propias | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-11 | Descargar un archivo autorizado | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-12 | Consultar el catálogo mediante una API pública | Consumidor de la API | Must | v0.2.0 | Aprobado |
| RF-13 | Gestionar el carrito mediante una API autenticada | Cliente de la API autenticado | Must | v0.3.0 | Propuesto |
| RF-14 | Ejecutar checkout, pago y consultas privadas mediante API | Cliente de la API autenticado | Must | v0.7.0 | Propuesto |
| RF-15 | Administrar el sistema mediante Django Admin | Administrador | Must | v0.9.0 | Aprobado |

Las decisiones transversales que deben aprobarse antes de crear el módulo se
encuentran en el
[checkpoint de decisiones del catálogo](catalog-decision-checkpoint.md).

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
CA-RF01-05 permanece pendiente. El modelo actual no tiene contrato ni campo para
el archivo maestro privado. Su verificación se difiere a RF-11, que definirá el
almacenamiento y la entrega autorizada.

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
| CA-RF01-05 | Pendiente: requiere contrato de archivo maestro privado | No aplica hasta RF-11 | No aplica | Pendiente, diferido a RF-11 |
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
| Estado | Implementado |
| Dependencias | RF-01, RF-02, RNF-03 a RNF-05, RNF-07, RNF-09 y RNF-11 |

#### Estado de preparación

Los conflictos previos quedaron cerrados el 2026-09-01:

- contrato y alcance aprobados en `3e30a7c`;
- ofertas asociadas a tipos de licencia inactivos excluidas en `3c58ae7`;
- carga de `license_type` sin N+1 verificada en `f3991b7`;
- trazabilidad previa consolidada en `9674d9b`.

Los siete criterios (CA-RF03-01 a CA-RF03-07) están implementados y
comprobados localmente. El código procesa `q`, `category`, `license` y
`ordering`; valida los parámetros conocidos y responde 400 ante valores
inválidos; pagina y conserva el estado de consulta; y la plantilla mantiene
visibles los controles con sus valores reconocidos. CA-RF03-01 a CA-RF03-06
siguen pendientes de evidencia formal y commit propio.

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
- Etiquetas múltiples, géneros jerárquicos y recomendaciones.
- Filtros por formato, frecuencia de muestreo y profundidad de bits.
- Ordenación por popularidad o comportamiento del usuario.
- Tamaño de página configurable por el consumidor.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | CA-RF03-01 a CA-RF03-06 implementadas y comprobadas localmente; CA-RF03-07 reutiliza pruebas de RF-01 |
| Decisiones aplicables | `docs/requirements/rf03-decision-checkpoint.md`, commit `3e30a7c` |
| Selector base disponible | `apps/catalog/selectors.py:get_available_products()`, `get_active_categories()`, `get_active_license_types()`, `ORDERING_OPTIONS` |
| Implementación web | `apps/catalog/views.py:product_list()` (búsqueda, filtros, orden, validación 400, conservación de estado) y `apps/catalog/templates/catalog/product_list.html` (controles visibles) |
| Consulta compartida | `apps/catalog/selectors.py:get_available_products()` |
| Implementación API | RF-12 |
| Evidencia | Puerta de calidad completa en `docs/evidence/RF-03/quality-gate-2026-09-01.md`; CA-RF03-07 en `docs/evidence/RF-03/CA-RF03-07.md`; CA-RF03-01 a CA-RF03-06 pendientes de evidencia individual por criterio |
| Commits de preparación | `3e30a7c`, `3c58ae7`, `f3991b7`, `9674d9b` |
| Commits de implementación | Pendientes (cambios todavía sin `git commit`) |

| Criterio | Prueba | Evidencia | Commit | Estado |
|---|---|---|---|---|
| CA-RF03-01 | `apps/catalog/tests/test_views.py::test_catalog_searches_available_products_by_normalized_text_case_insensitively` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-02 | `apps/catalog/tests/test_views.py::test_catalog_filters_available_products_by_category_and_license_slug` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-03 | `apps/catalog/tests/test_views.py::test_catalog_orders_available_products_by_minimum_price_with_stable_tiebreak` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-04 | `apps/catalog/tests/test_views.py::test_catalog_pagination_link_preserves_only_search_filters_and_ordering` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-05 | `apps/catalog/tests/test_views.py::test_catalog_renders_category_and_license_selects_with_active_options_and_recognized_value`, `test_catalog_shows_message_and_keeps_all_recognized_controls_visible_when_query_has_no_matches` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-06 | `apps/catalog/tests/test_views.py::test_catalog_returns_400_for_an_unrecognized_ordering_value`, `test_catalog_orders_available_products_by_name_in_descending_order`, `test_catalog_returns_400_for_an_unrecognized_category_slug`, `test_catalog_returns_400_for_an_unrecognized_license_slug`, `test_catalog_returns_400_instead_of_404_when_an_invalid_category_and_an_invalid_page_are_combined` | `docs/evidence/RF-03/quality-gate-2026-09-01.md` | Pendiente | Implementado y comprobado localmente |
| CA-RF03-07 | `apps/catalog/tests/test_views.py` (pruebas 404/200 reutilizadas de RF-01) | `docs/evidence/RF-03/CA-RF03-07.md` | `c8e2a20` | Verificado: Green preexistente de RF-01 |

Nota resuelta: la validación de `category`/`license` inválidos (RN-RF03-08) y
la precedencia de FE-01 sobre FE-02 quedan registradas como parte del texto
ampliado de CA-RF03-06 (ver arriba), no como un criterio nuevo.

CA-RF03-07 reutiliza la paginación y las pruebas 404 implementadas por RF-01;
no se revierte comportamiento correcto para fabricar un Red. Los siete
criterios aprobados están implementados y comprobados localmente mediante la
batería de pruebas indicada. La puerta de calidad completa se ejecutó el
2026-09-01 con resultado favorable en las nueve comprobaciones (`manage.py
check`, `makemigrations --check --dry-run`, `migrate --check`, `pytest -q`
con `41 passed`, `ruff check`, `ruff format --check`, `pip check`, `git diff
--check` y `git status --short`), registrado en
`docs/evidence/RF-03/quality-gate-2026-09-01.md`. RF-03 permanece en estado
`Implementado`; no se declara `Verificado` porque falta evidencia individual
por criterio para CA-RF03-01 a CA-RF03-06, la nota anterior sobre RN-RF03-08
sigue sin resolver, y ningún cambio de este cierre tiene todavía un commit
asociado.

## RF-04: Registrarse, iniciar sesión y cerrar sesión

## RF-05: Gestionar productos del carrito privado

## RF-06: Convertir el carrito en un pedido histórico

## RF-07: Simular un pago aprobado de forma independiente

## RF-08: Simular un pago fallido y reintentarlo

## RF-09: Consultar los pedidos propios

## RF-10: Consultar las licencias propias

## RF-11: Descargar un archivo autorizado

### RF-12 — Consultar el catálogo mediante una API pública

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Consumidor de la API |
| Prioridad | Must |
| Versión objetivo | v0.2.0 |
| Estado | Aprobado |
| Dependencias | RF-01, RF-02, RF-03, RNF-01, RNF-03 a RNF-07 y RNF-09 a RNF-11 |

#### Objetivo

Exponer una interfaz REST pública, de solo lectura y versionada para consultar
la misma selección de productos disponible en la web.

#### Contrato HTTP propuesto

| Operación | Ruta | Resultado |
|---|---|---|
| Listar | `GET /api/v1/catalog/products/` | Página de productos activos |
| Consultar detalle | `GET /api/v1/catalog/products/{slug}/` | Producto, preview y licencias |
| Metadatos HTTP | `HEAD` u `OPTIONS` sobre las rutas anteriores | Respuesta estándar DRF |

La lista acepta los parámetros válidos de RF-03. La página tiene 12 elementos
y usa la estructura `count`, `next`, `previous` y `results`.

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

La lista contiene:

- `name`, `slug`, `summary` y categoría pública;
- duración y características técnicas;
- precio mínimo y moneda;
- resumen de las licencias disponibles;
- URL pública del detalle de API.

El detalle añade:

- descripción completa;
- URL de preview pública, si está disponible;
- ofertas de licencia activas con destino, resumen, precio y moneda.

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

#### Pruebas previstas

- Acceso anónimo explícitamente permitido.
- Lista, detalle, filtros, orden y paginación equivalentes a la web.
- Esquema de paginación y códigos 200, 400, 404 y 405.
- Exclusión de productos y ofertas no disponibles.
- Ausencia de campos y URLs privadas en toda respuesta.
- Número acotado de consultas durante la serialización.

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
| Pruebas | Pendiente hasta v0.2.0 |
| Selectores | RF-01 y RF-03; pendiente |
| Serializers y vistas | Pendiente |
| Evidencia | Pendiente |
| Commit | Pendiente |

## RF-13: Gestionar el carrito mediante una API autenticada

## RF-14: Ejecutar checkout, pago y consultas privadas mediante API

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
