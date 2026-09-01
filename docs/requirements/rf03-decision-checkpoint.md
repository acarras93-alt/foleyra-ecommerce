# Checkpoint de decisiones de RF-03

## Estado y alcance

- Fecha de aprobación: 2026-09-01.
- Estado: aprobado para resolver conflictos previos; los criterios CA-RF03-01 a
  CA-RF03-06 continúan sin implementar.
- Requisito afectado: RF-03.
- Responsable de aprobación: propietario del repositorio, mediante solicitud
  explícita de resolver los conflictos antes de iniciar los criterios.

Este checkpoint concreta el contrato de consulta sin copiar marca, contenido,
diseño ni modelo comercial de terceros. La página pública de efectos de sonido
de Epidemic Sound se utilizó solo como referencia de producto: presenta
categorías visibles, títulos descriptivos, duración y navegación desde una
categoría hacia sonidos concretos. Foleyra mantiene su venta unitaria por
ofertas de licencia, aprobada en D-CAT-01 y D-CAT-02.

Referencia observada:
`https://www.epidemicsound.com/es/sound-effects/`.

## D-RF03-01 — Límite entre web y API

RF-03 implementará primero el contrato web sobre `GET /catalog/`. La validación
HTTP web no se construirá con DRF. RF-12 añadirá después la API pública y
reutilizará el selector de consulta, pero validará y representará sus errores en
su propia capa.

Un Red causado únicamente por solicitar una ruta `/api/` inexistente no cuenta
como Red de RF-03 porque adelantaría RF-12.

## D-RF03-02 — Búsqueda textual

`q` se define así:

1. se eliminan espacios exteriores y se agrupan espacios interiores
   consecutivos;
2. el límite de 100 caracteres se comprueba después de normalizar;
3. el valor vacío equivale a omitir la búsqueda;
4. la frase completa se compara sin distinguir mayúsculas con `Product.name`,
   `Product.summary` y `Product.description`;
5. coincidir en cualquiera de los tres campos incluye el producto;
6. no se implementan stemming, tolerancia ortográfica, búsqueda semántica ni
   texto completo de PostgreSQL en v0.2.0.

Esta decisión resuelve la diferencia terminológica entre “descripción breve”,
`summary` y `description` sin dejar contenido descriptivo público fuera de la
búsqueda.

## D-RF03-03 — Filtros incluidos en v0.2.0

RF-03 admite únicamente:

- `category`, por `Category.slug` activo;
- `license`, por `LicenseType.slug` activo.

Los valores vacíos omiten el filtro. Un `slug` inexistente o inactivo es un
valor conocido inválido y produce 400.

Los filtros por formato, frecuencia de muestreo y profundidad de bits quedan
fuera de v0.2.0. Los metadatos técnicos continúan visibles en el detalle, pero
la referencia de catálogo prioriza descubrimiento por categorías y títulos, y
los criterios aprobados de RF-03 no exigían esos tres filtros.

## D-RF03-04 — Disponibilidad de una licencia

Una oferta es pública solo cuando se cumplen simultáneamente:

- producto activo;
- categoría activa;
- oferta activa;
- tipo de licencia activo.

`LicenseType.is_active` no puede ser un campo administrativo sin efecto. Un
producto con una única oferta activa asociada a un tipo de licencia inactivo no
es disponible. Si conserva otra oferta y tipo activos, el producto sigue siendo
disponible, pero la licencia inactiva no participa en filtros, precio mínimo ni
detalle público.

Esta regla pertenece al selector base heredado de RF-01 y RF-02. Debe corregirse
mediante un ciclo test-first previo y no se registrará como implementación de
CA-RF03-02 o CA-RF03-03.

## D-RF03-05 — Precio mínimo y filtro de licencia

El precio `Desde` es el mínimo global de las ofertas públicas del producto. El
filtro `license` comprueba que el producto ofrece ese destino de uso, pero no
cambia la tarjeta para mostrar el precio de la licencia filtrada.

Por ejemplo, si un producto ofrece una licencia social por 10 EUR y publicidad
por 30 EUR, filtrar publicidad conserva `Desde 10 EUR`. Las ofertas o tipos de
licencia inactivos nunca intervienen en ese mínimo.

`price` y `-price` ordenarán por ese mismo valor y añadirán `pk` ascendente como
desempate estable.

## D-RF03-06 — Validación segura de parámetros

- Los valores conocidos inválidos producen 400 y señalan el parámetro sin
  detalles internos.
- `ordering` usa un mapa constante para `name`, `-name`, `price` y `-price`; el
  texto recibido nunca se entrega directamente a `order_by()`.
- Los parámetros desconocidos se ignoran. No se copian al selector ni a los
  enlaces de paginación.
- La conservación de estado incluye solo `q`, `category`, `license` y
  `ordering`; `page` se sustituye al construir cada enlace.

Ignorar parámetros desconocidos permite que un enlace con parámetros de
campaña o analítica siga abriendo el catálogo sin ampliar el contrato ORM.

## D-RF03-07 — Página vacía y 404 preexistente

- La página 1 de una consulta válida sin resultados responde 200.
- Una página posterior a la última, no numérica o menor que uno responde 404.
- El comportamiento 404 ya fue implementado y probado por RF-01 en el commit
  `c8e2a20`.

RNF-03 exige Red para comportamiento nuevo. Por tanto, CA-RF03-07 se registrará
como Green preexistente con regresión y evidencia; no se revierte código correcto
ni se fabrica un fallo.

## D-RF03-08 — Controles y dependencias

La página mantendrá visibles los controles y los valores reconocidos tanto en
resultados como en estado vacío. No se añade `django-filter` en v0.2.0. La capa
web podrá usar formularios Django para validar y conservar valores; el selector
compartido recibirá únicamente datos ya normalizados.

No se autoriza todavía a crear el formulario, extender el selector ni modificar
la plantilla. Cada criterio debe iniciar después su ciclo test-first propio.

## Conflictos técnicos previos autorizados

Antes de CA-RF03-01 se resolverán de forma independiente:

1. exclusión de ofertas asociadas a tipos de licencia inactivos;
2. carga acotada de `license_type` para evitar N+1;
3. trazabilidad de los commits ya existentes de RF-02;
4. registro de CA-RF03-07 como Green preexistente.

Al terminar estos puntos, RF-03 seguirá sin búsqueda, filtros, ordenación por
parámetro ni conservación del estado de consulta.
