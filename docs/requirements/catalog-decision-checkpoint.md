# Checkpoint de decisiones del catálogo v0.2.0

## Estado y finalidad

- Fecha de revisión: 2026-08-25.
- Estado: aprobado para iniciar la implementación test-first del catálogo
  v0.2.0.
- Requisitos afectados: RF-01, RF-02, RF-03, RF-12 y RF-15.
- Objetivo: cerrar el contrato del dominio antes de continuar la implementación
  test-first de `apps.catalog`.
- Responsable de aprobación: `acarras93-alt`, propietario del repositorio.

Este documento convierte las referencias visuales en decisiones de producto.
Las capturas orientan la jerarquía de categorías, el detalle técnico y la
separación de licencias por destino de uso; no convierten Foleyra en un servicio
de suscripción ni autorizan a copiar contenido, marca o diseño de terceros.

## Lenguaje del dominio aprobado

- **Producto sonoro:** contenido digital que se descubre en el catálogo. Define
  el audio y sus características técnicas; no representa por sí solo el derecho
  de uso.
- **Categoría:** agrupación principal de productos, por ejemplo ambiente, agua,
  vehículos o interfaz de usuario. En v0.2.0 cada producto tiene una categoría.
- **Tipo de licencia:** permiso comercial definido por el destino de uso, por
  ejemplo YouTube/redes sociales, producción cinematográfica o publicidad.
- **Oferta de licencia:** relación vendible entre un producto y un tipo de
  licencia. Contiene precio, moneda y estado.
- **Preview:** archivo promocional público, preparado de forma independiente.
- **Archivo maestro:** archivo privado que solo podrá descargarse después de una
  compra y autorización válidas.

La palabra **plataforma** significa aquí canal o destino cubierto por la
licencia. No significa iOS, Android, macOS o Windows y tampoco describe la
compatibilidad técnica del archivo.

## Modelo mínimo aprobado

| Entidad | Responsabilidad | Datos principales |
|---|---|---|
| `Category` | Clasificar el catálogo | nombre, `slug`, descripción, `is_active` |
| `Product` | Describir el contenido sonoro | SKU, nombre, `slug`, resúmenes, categoría, duración, formato, frecuencia, profundidad, preview, maestro y estado |
| `LicenseType` | Definir un permiso por destino de uso | nombre, `slug`, destino, resumen, versión de términos y estado |
| `ProductLicenseOffer` | Hacer vendible una combinación | producto, licencia, precio decimal, moneda y estado |

Relaciones aprobadas:

```text
Category 1 ─── N Product 1 ─── N ProductLicenseOffer N ─── 1 LicenseType
```

Restricciones mínimas:

- SKU y `slug` de producto únicos.
- `slug` de categoría y de licencia únicos.
- precio mayor o igual que cero, almacenado con `DecimalField`.
- una sola oferta por combinación de producto y tipo de licencia.
- categoría protegida frente al borrado mientras tenga productos.
- producto o licencia con referencias históricas protegidos frente al borrado.
- duración, frecuencia de muestreo y profundidad de bits positivas.
- moneda fijada a EUR durante el MVP.

## Decisiones aprobadas antes de continuar el código

### D-CAT-01 — Venta unitaria, no suscripción

**Estado:** aprobada el 2026-08-21.

**Decisión:** cada compra adquiere una licencia concreta para un producto. No
existen planes mensuales, descargas ilimitadas ni stock.

**Por qué:** coincide con el alcance académico, reduce estados recurrentes y
mantiene el recorrido carrito → pedido → pago → licencia → descarga.

**Consecuencia:** las capturas de precios por suscripción solo sirven como
referencia para presentar licencias; no definen el modelo comercial de Foleyra.
Los planes mensuales quedan fuera del MVP y podrán evaluarse en una evolución
posterior.

### D-CAT-02 — Separar producto, licencia y oferta

**Estado:** aprobada el 2026-08-25.

**Decisión:** utilizar las cuatro entidades del modelo mínimo. El precio
pertenece a `ProductLicenseOffer`, no a `Product` ni a `LicenseType`.

**Por qué:** el mismo audio puede venderse para varios destinos con condiciones
y precios distintos. Una licencia también puede reutilizarse en varios
productos.

**Consecuencia:** la tarjeta de catálogo muestra el precio mínimo activo como
`Desde X EUR`; el detalle muestra todas las ofertas activas.

### D-CAT-03 — Destinos iniciales de licencia

**Estado:** aprobada el 2026-08-25.

**Decisión para v0.2.0:** cargar como datos, no como valores rígidos de código,
estos tres tipos iniciales:

1. YouTube y redes sociales;
2. producciones cinematográficas;
3. publicidad.

**Por qué:** cubren las referencias aportadas y pueden administrarse sin crear
una migración cuando cambie el catálogo. Podcast, web, videojuegos o emisión se
añadirán solo si el alcance los necesita.

YouTube y redes sociales comparten un mismo tipo de licencia durante el MVP.
Separarlos en el futuro requerirá una nueva decisión de producto, pero no una
modificación del esquema.

### D-CAT-04 — Características del archivo adquirido

**Estado:** aprobada el 2026-08-25.

**Decisión:** guardar en el producto:

- `duration_ms`, como entero para evitar imprecisión con efectos cortos;
- `audio_format`, inicialmente WAV, FLAC o AIFF;
- `sample_rate_hz`, por ejemplo 44100, 48000 o 96000;
- `bit_depth`, por ejemplo 16, 24 o 32 bits.

Estos campos describen el maestro adquirido. La preview puede usar otro formato
y calidad, que no deben confundirse con lo comprado. El MVP admite WAV, FLAC y
AIFF; los valores iniciales de frecuencia son 44100, 48000 o 96000 Hz y las
profundidades iniciales son 16, 24 o 32 bits. La fixture de demostración partirá
de WAV, 48000 Hz y 24 bits.

### D-CAT-05 — Política de preview

**Estado:** aprobada el 2026-08-25.

**Decisión:** la preview se prepara manualmente fuera de Django y se carga
como MP3 público, con marca audible y duración máxima de 30 segundos o la
duración del producto si esta es menor. El MVP no transcodifica ni genera formas
de onda.

**Riesgo:** un efecto muy corto puede reproducirse completo; la marca audible es
la protección principal. La aplicación nunca debe utilizar el maestro como
fallback.

La calidad concreta de codificación puede ajustarse sin cambiar el contrato
mientras la preview siga siendo un MP3 promocional independiente, con marca
audible y sin utilizar nunca el maestro como alternativa.

### D-CAT-06 — Separación de almacenamiento público y privado

**Estado:** principio aprobado el 2026-08-25; detalle de entrega diferido a
RF-11.

**Decisión:** previews y archivos maestros usan raíces de almacenamiento
distintas. Solo la raíz de previews puede servirse públicamente en desarrollo.
El maestro se entregará mediante una vista autorizada en RF-11, nunca mediante
una URL de medios pública.

**Por qué:** omitir un campo del template o serializer no protege un directorio
que el servidor ya publica.

La raíz privada concreta y la estrategia de entrega se definirán antes de
RF-11. Este detalle diferido no bloquea la estructura lógica del catálogo.

### D-CAT-07 — Contrato público y paginación

**Estado:** aprobada el 2026-08-25.

**Decisión:** utilizar:

- web en `/catalog/` y `/catalog/{slug}/`;
- API en `/api/v1/catalog/products/` y su detalle por `slug`;
- 12 elementos por página, sin tamaño configurable;
- orden inicial por nombre e identificador;
- página inválida o inexistente con respuesta 404;
- filtro conocido inválido con respuesta 400;
- lista válida sin resultados con respuesta 200 y estado vacío.

**Por qué:** un contrato único hace comparables web y API y permite pruebas
deterministas.

### D-CAT-08 — Administración necesaria para v0.2.0

RF-15 figura actualmente con versión objetivo v0.9.0, pero RF-01 necesita una
forma reproducible de cargar categorías, productos, licencias y ofertas.

**Estado:** aprobada el 2026-08-25.

**Decisión:** mantener RF-15 íntegramente en v0.9.0 y utilizar en v0.2.0 una
fixture pequeña de demostración con datos ficticios. La fixture permite
reproducir la comprobación manual y las evidencias de RF-01 sin adelantar
permisos o comportamientos administrativos.

Las pruebas automáticas no dependerán de esa fixture: crearán sus propios datos
aislados. La carga de demostración no constituye implementación de RF-15.

### D-CAT-09 — Historia de compra inmutable

**Estado:** principio aprobado el 2026-08-25; implementación diferida a RF-06.

**Decisión:** cuando se implemente RF-06, cada línea de pedido copiará SKU,
nombre, licencia, versión de términos, precio y moneda. No dependerá de los
valores actuales del catálogo.

**Por qué:** cumple RN-RF01-05 y permite retirar o modificar productos sin
reescribir compras anteriores.

Esta decisión no autoriza todavía modelos de pedidos.

## Decisiones que pueden diferirse

- taxonomía jerárquica y múltiples categorías por producto;
- múltiples archivos maestros o formatos seleccionables por una misma compra;
- almacenamiento en nube, CDN y URLs firmadas;
- búsqueda de texto completo de PostgreSQL;
- licencias de suscripción o planes para empresas;
- forma de onda y procesamiento automático de audio;
- múltiples monedas e impuestos.

No deben añadirse campos o dependencias para estos casos durante v0.2.0.

## Criterio de aprobación

El checkpoint queda aprobado con el siguiente resultado:

- [x] D-CAT-01 confirma venta unitaria, sin suscripción ni stock.
- [x] D-CAT-02 confirma la separación entre producto, licencia y oferta, y el
  precio de la oferta.
- [x] D-CAT-03 confirma los destinos iniciales.
- [x] D-CAT-04 confirma formatos y valores técnicos iniciales.
- [x] D-CAT-05 confirma la política de preview.
- [x] D-CAT-06 confirma la separación lógica entre almacenamiento público y
  privado; el mecanismo de entrega se concretará en RF-11.
- [x] D-CAT-07 confirma rutas, paginación y errores.
- [x] D-CAT-08 resuelve la carga mediante una fixture de demostración.
- [x] D-CAT-09 confirma la instantánea histórica; sus modelos se crearán en
  RF-06.
- [x] RNF-06 a RNF-11 están aceptados como puerta de calidad del catálogo.
- [x] RF-01, RF-02, RF-03 y RF-12 constan como `Aprobado` con fecha y
  responsable registrados en la bitácora.
- [x] RF-15 consta como `Aprobado`, pero su implementación completa permanece
  planificada para v0.9.0.
- [x] La primera migración prevista se revisó antes de aplicarla.

La aprobación permite comenzar la implementación test-first. No implica que el
código cubra las decisiones ni que los RF estén verificados: cada criterio debe
recorrer Red, Green, regresión y evidencia real.

## Estado de cobertura técnica al aprobar

| Decisión | Estado de decisión | Cobertura técnica actual |
|---|---|---|
| D-CAT-01 | Aprobada | Parcial: existe la oferta unitaria; la compra pertenece a RF-06 |
| D-CAT-02 | Aprobada | Parcial: existen los modelos; faltan selectores e interfaces |
| D-CAT-03 | Aprobada | Pendiente de fixture de demostración |
| D-CAT-04 | Aprobada | Parcial: existen campos; faltan pruebas de valores admitidos |
| D-CAT-05 | Aprobada | Parcial: existe `preview_file`; faltan política y almacenamiento |
| D-CAT-06 | Principio aprobado | Implementación privada diferida a RF-11 |
| D-CAT-07 | Aprobada | No implementada |
| D-CAT-08 | Aprobada | Fixture pendiente de creación |
| D-CAT-09 | Principio aprobado | Implementación diferida a RF-06 |

## Explicación breve para la defensa

1. Foleyra no maneja stock porque vende derechos de uso sobre archivos
   digitales, no unidades físicas.
2. Producto y licencia se separan porque el mismo audio admite destinos y
   precios diferentes.
3. La oferta une ambos conceptos y permite mostrar un precio mínimo sin perder
   el precio concreto que se comprará.
4. Preview y maestro se separan por diseño y por almacenamiento; ocultar un
   campo en HTML o JSON no basta para proteger el archivo.
5. Web y API reutilizarán el mismo selector de productos disponibles, de modo
   que filtros, estados y optimización N+1 no diverjan.
6. Los pedidos futuros guardarán una instantánea para que una edición del
   catálogo no cambie una compra pasada.
7. Django Admin será una interfaz autorizada; las reglas del negocio seguirán
   viviendo en modelos, validaciones y servicios compartidos.

## Alineación pendiente del manual antiguo

Antes de seguir literalmente el notebook
`Manual_Django_Ecommerce/MANUAL_DJANGO_ECOMMERCE_SONORO_v0.2.ipynb` deben
corregirse estas diferencias:

- el manual define el producto como una licencia y coloca un único precio en el
  producto;
- usa `accounts` mientras el repositorio aprobado utiliza `apps.users`;
- enumera Django Admin como RF-13, mientras la fuente vigente lo identifica como
  RF-15;
- contiene versiones y fragmentos preparatorios anteriores al bloqueo actual de
  dependencias;
- pospone el archivo adquirido, aunque los RF vigentes ya exigen definir su
  privacidad desde el catálogo.

El manual sigue siendo una guía didáctica, pero los requisitos, ADR, versiones
bloqueadas y código del repositorio son la fuente de verdad.

## Referencias técnicas

- [Vistas genéricas de listado y detalle en Django 5.2](https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-display/)
- [`select_related()` y `prefetch_related()` en Django 5.2](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related)
- [Vistas genéricas y prevención de N+1 en DRF](https://www.django-rest-framework.org/api-guide/generic-views/)
- [Paginación por número de página en DRF](https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination)
- [Permiso público explícito `AllowAny`](https://www.django-rest-framework.org/api-guide/permissions/#allowany)
- [Configuración de Django Admin 5.2](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/)
