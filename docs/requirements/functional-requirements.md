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
| RF-03 | Buscar, filtrar, ordenar y paginar el catálogo | Visitante o cliente | Should | v0.2.0 | Aprobado |
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
   categoría activa y con alguna oferta de licencia activa.
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
- RN-RF01-02: un producto sin categoría activa o sin oferta de licencia activa
  no se considera disponible para compra y no aparece.
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

| Elemento | Referencia |
|---|---|
| Pruebas | Pendiente hasta v0.2.0 |
| Implementación web | Pendiente |
| Implementación API | RF-12 |
| Evidencia | Pendiente |
| Commit | Pendiente |

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

- El producto, su categoría y al menos una oferta de licencia están activos.
- Existe un `slug` público y único para el producto.
- Existe una preview pública y es un archivo distinto del maestro.

#### Disparador

El visitante selecciona un producto desde el catálogo o solicita su URL de
detalle.

#### Flujo principal

1. El sistema localiza el producto activo por su `slug`.
2. El sistema carga su categoría y sus ofertas de licencia activas.
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
- FE-02: si el producto, su categoría o todas sus ofertas están inactivos, el
  sistema responde con 404 aunque el visitante conozca la URL anterior.

#### Reglas de negocio

- RN-RF02-01: el detalle es público para usuarios anónimos y autenticados.
- RN-RF02-02: solo se muestran ofertas de licencia activas.
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
| Pruebas | Pendiente hasta v0.2.0 |
| Implementación web | Pendiente |
| Consulta compartida | Pendiente; debe reutilizar RF-01 |
| Implementación API | RF-12 |
| Evidencia | Pendiente |
| Commit | Pendiente |

### RF-03 — Buscar, filtrar, ordenar y paginar el catálogo

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Should |
| Versión objetivo | v0.2.0 |
| Estado | Aprobado |
| Dependencias | RF-01, RF-02, RNF-03 a RNF-05, RNF-07, RNF-09 y RNF-11 |

#### Objetivo

Permitir que el visitante reduzca y ordene el catálogo público mediante un
contrato de consulta limitado, comprensible y reutilizable por la web y la API.

#### Contrato de consulta propuesto

| Parámetro | Finalidad | Valores admitidos |
|---|---|---|
| `q` | Buscar en nombre y descripción breve | Texto de hasta 100 caracteres |
| `category` | Filtrar categoría | `slug` de categoría activa |
| `license` | Filtrar destino de licencia | `slug` de licencia activa |
| `format` | Filtrar formato maestro | Valor publicado por el catálogo |
| `sample_rate` | Filtrar frecuencia | Entero positivo en Hz |
| `bit_depth` | Filtrar profundidad | Entero positivo en bits |
| `ordering` | Ordenar | `name`, `-name`, `price`, `-price` |
| `page` | Seleccionar página | Entero positivo |

#### Precondiciones

- RF-01 está disponible.
- Los filtros se aplican siempre sobre el conjunto de productos disponibles,
  nunca sobre productos administrativos o inactivos.

#### Disparador

El visitante envía uno o varios parámetros desde los controles del catálogo.

#### Flujo principal

1. El sistema normaliza espacios del texto de búsqueda.
2. El sistema valida únicamente los parámetros conocidos.
3. El sistema parte de la consulta pública definida por RF-01.
4. El sistema aplica búsqueda y filtros combinándolos mediante una condición
   lógica `AND`.
5. El sistema aplica exclusivamente un orden permitido y añade el identificador
   como desempate estable.
6. El sistema pagina 12 productos y conserva los filtros al cambiar de página.
7. La página muestra los filtros activos y el número total de resultados.

#### Flujos alternativos y errores

- FA-01: una búsqueda sin coincidencias muestra un estado vacío contextual.
- FA-02: `q` vacío equivale a no aplicar búsqueda.
- FE-01: un valor inválido de un parámetro conocido responde 400 y señala el
  parámetro, sin incluir detalles internos.
- FE-02: una página inexistente, no numérica o menor que uno responde 404.

#### Reglas de negocio

- RN-RF03-01: los filtros nunca permiten recuperar un producto no disponible.
- RN-RF03-02: la búsqueda no distingue mayúsculas de minúsculas.
- RN-RF03-03: ordenar por precio utiliza el precio mínimo de las ofertas activas.
- RN-RF03-04: los valores de ordenación pertenecen a una lista cerrada; no se
  convierten parámetros del usuario directamente en expresiones ORM.
- RN-RF03-05: el orden siempre es determinista para impedir duplicados o saltos
  entre páginas.
- RN-RF03-06: web y API reutilizan la misma construcción de consulta, aunque
  cada interfaz valide y represente sus errores en su propia capa HTTP.

#### Criterios de aceptación

- CA-RF03-01: dada una palabra contenida en el nombre o descripción, cuando se
  busca, entonces solo aparecen productos disponibles coincidentes.
- CA-RF03-02: dados filtros de categoría y licencia, cuando se combinan,
  entonces solo aparecen productos que cumplen ambos.
- CA-RF03-03: cuando se ordena por precio ascendente o descendente, entonces se
  usa el precio mínimo activo y el orden es estable.
- CA-RF03-04: cuando se cambia de página, entonces se conservan la búsqueda,
  filtros y orden actuales.
- CA-RF03-05: dada una consulta válida sin coincidencias, entonces se muestra un
  mensaje comprensible y se conservan los controles de búsqueda.
- CA-RF03-06: dado un valor no permitido en `ordering`, entonces la respuesta es
  400 y no se ejecuta una ordenación arbitraria.
- CA-RF03-07: dada una página inexistente o inválida, entonces la respuesta es
  404.

#### Pruebas previstas

- Búsqueda por nombre y descripción sin distinguir mayúsculas.
- Combinación de categoría, licencia y características técnicas.
- Exclusión de productos, categorías y ofertas inactivos.
- Cada opción permitida de ordenación y su desempate estable.
- Rechazo de valores de ordenación no permitidos.
- Persistencia de parámetros en enlaces de paginación.
- Estado vacío contextual y página inexistente.
- Número acotado de consultas al combinar relaciones y paginación.

#### Evidencias previstas

- `docs/evidence/RF-03/catalogo-filtrado.png`
- `docs/evidence/RF-03/catalogo-sin-resultados.png`
- Resultado de las pruebas asociadas.

#### Fuera de alcance

- Autocompletado, tolerancia a errores ortográficos y búsqueda semántica.
- Etiquetas múltiples, géneros jerárquicos y recomendaciones.
- Ordenación por popularidad o comportamiento del usuario.
- Tamaño de página configurable por el consumidor.

#### Trazabilidad

| Elemento | Referencia |
|---|---|
| Pruebas | Pendiente hasta v0.2.0 |
| Implementación web | Pendiente |
| Consulta compartida | Pendiente; extensión de RF-01 |
| Implementación API | RF-12 |
| Evidencia | Pendiente |
| Commit | Pendiente |

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
