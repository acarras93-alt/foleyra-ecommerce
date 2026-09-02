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
| RF-03 | Buscar, filtrar, ordenar y paginar el catálogo | Visitante o cliente | Should | v0.2.0 | Verificado |
| RF-04 | Registrarse, iniciar sesión y cerrar sesión | Visitante o cliente | Must | v0.3.0 | Verificado |
| RF-05 | Gestionar los productos del carrito privado | Cliente autenticado | Must | v0.3.0 | Aprobado |
| RF-06 | Convertir el carrito en un pedido histórico | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-07 | Simular un pago aprobado de forma independiente | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-08 | Simular un pago fallido y reintentarlo | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-09 | Consultar los pedidos propios | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-10 | Consultar las licencias propias | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-11 | Descargar un archivo autorizado | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-12 | Consultar el catálogo mediante una API pública | Consumidor de la API | Must | v0.2.0 | Verificado |
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
| Estado | Verificado |
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
- Etiquetas múltiples, géneros jerárquicos y recomendaciones.
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
Todavía no existen implementación, pruebas ejecutadas ni evidencias reales.

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
