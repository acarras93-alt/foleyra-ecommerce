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
| RF-01 | Consultar el catálogo | Visitante o cliente | Must | v0.2.0 | Propuesto |
| RF-02 | Consultar el detalle y escuchar una preview pública | Visitante o cliente | Must | v0.2.0 | Propuesto |
| RF-03 | Buscar, filtrar, ordenar y paginar el catálogo | Visitante o cliente | Should | v0.2.0 | Propuesto |
| RF-04 | Registrarse, iniciar sesión y cerrar sesión | Visitante o cliente | Must | v0.3.0 | Propuesto |
| RF-05 | Gestionar los productos del carrito privado | Cliente autenticado | Must | v0.3.0 | Propuesto |
| RF-06 | Convertir el carrito en un pedido histórico | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-07 | Simular un pago aprobado de forma independiente | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-08 | Simular un pago fallido y reintentarlo | Cliente autenticado | Must | v0.5.0 | Propuesto |
| RF-09 | Consultar los pedidos propios | Cliente autenticado | Must | v0.4.0 | Propuesto |
| RF-10 | Consultar las licencias propias | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-11 | Descargar un archivo autorizado | Cliente autenticado | Must | v0.6.0 | Propuesto |
| RF-12 | Consultar el catálogo mediante una API pública | Consumidor de la API | Must | v0.2.0 | Propuesto |
| RF-13 | Gestionar el carrito mediante una API autenticada | Cliente de la API autenticado | Must | v0.3.0 | Propuesto |
| RF-14 | Ejecutar checkout, pago y consultas privadas mediante API | Cliente de la API autenticado | Must | v0.7.0 | Propuesto |
| RF-15 | Administrar el sistema mediante Django Admin | Administrador | Must | v0.9.0 | Propuesto |


## 4. Especificación detallada

### RF-01 — Consultar catálogo de productos activos

#### Metadatos

| Campo | Valor |
|---|---|
| Actor principal | Visitante o cliente |
| Prioridad | Must |
| Versión objetivo | v0.2.0 |
| Estado | Propuesto |
| Dependencias | RNF-01, RNF-04 y RNF-05 |

#### Objetivo

Permitir que cualquier visitante consulte los productos sonoros
disponibles para su compra, sin necesidad de autenticarse.

#### Precondiciones

- La aplicación está disponible.
- La conexión con PostgreSQL funciona.
- El catálogo puede contener cero o más productos activos.

#### Disparador

El visitante accede a la página pública del catálogo.

#### Flujo principal

1. El visitante solicita la página del catálogo.
2. El sistema consulta únicamente los productos activos.
3. El sistema carga la categoría asociada a cada producto.
4. El sistema ordena y pagina los resultados.
5. La página muestra los metadatos públicos de cada producto.
6. El visitante puede acceder al detalle de un producto.

#### Flujos alternativos y errores

- FA-01: si no existen productos activos, el sistema muestra un estado vacío.
- FA-02: si existen más resultados que el límite de página, se muestra paginación.
- FE-01: si se solicita una página inexistente, el sistema responde con un error 404.

#### Reglas de negocio

- RN-RF01-01: los productos inactivos no aparecen en el catálogo.
- RN-RF01-02: no es necesario iniciar sesión para consultar el catálogo.
- RN-RF01-03: el archivo sonoro completo nunca se expone públicamente.
- RN-RF01-04: los cambios del catálogo no modifican pedidos anteriores.
- RN-RF01-05: la consulta debe evitar accesos repetidos innecesarios a categorías.

#### Criterios de aceptación

- CA-RF01-01: dado un producto activo, cuando un visitante abre el catálogo,
  entonces el producto aparece en los resultados.
- CA-RF01-02: dado un producto inactivo, cuando se consulta el catálogo,
  entonces el producto no aparece.
- CA-RF01-03: dado un catálogo vacío, cuando un visitante accede,
  entonces se muestra un mensaje comprensible y no un error.
- CA-RF01-04: dado un catálogo con varias páginas, cuando el usuario cambia
  de página, entonces recibe el bloque de resultados correspondiente.
- CA-RF01-05: cuando se muestra el catálogo, no se publica ninguna URL
  correspondiente al archivo privado completo.

#### Datos y permisos

Datos públicos:

- nombre;
- categoría;
- precio;
- moneda;
- duración;
- formato;
- resumen de licencia.

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

## RF-02: Consultar detalle y escuchar preview pública

## RF-03: Buscar, filtrar, ordenar y paginar el catálogo

## RF-04: Registrarse, iniciar sesión y cerrar sesión

## RF-05: Gestionar productos del carrito privado

## RF-06: Convertir el carrito en un pedido histórico

## RF-07: Simular un pago aprobado de forma independiente

## RF-08: Simular un pago fallido y reintentarlo

## RF-09: Consultar los pedidos propios

## RF-10: Consultar las licencias propias

## RF-11: Descargar un archivo autorizado

## RF-12: Consultar el catálogo mediante una API pública

## RF-13: Gestionar el carrito mediante una API autenticada

## RF-14: Ejecutar checkout, pago y consultas privadas mediante API

## RF-15: Administrar el sistema mediante Django Admin