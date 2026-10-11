# Foleyra — Criterios restantes del MVP y metodología

Fuentes actualizadas en el repositorio: [requisitos funcionales](docs/requirements/functional-requirements.md) y [plan de cierre](docs/requirements/mvp-implementation-plan.md).

**Copia histórica del 2026-09-27.** Se conserva como material de planificación;
sus estados, contratos y método no representan el código actual. Para trabajar
un criterio, utilizar los documentos enlazados arriba y la premisa del 2026-10-07.

# Plan de cierre del MVP y metodología por criterio

Fecha de revisión: 2026-09-27. Base de código: `70842ca`.

## 1. Estado comprobado antes de planificar

La base permite descubrir productos, gestionar una cuenta y un carrito privado,
crear un pedido pendiente y consultar su historia. Todavía no completa pago,
emisión de derechos y entrega del archivo adquirido.

| Área | Código observado | Qué falta para el recorrido completo |
|---|---|---|
| Catálogo y API pública | Modelos, selectores, web, previews y endpoints públicos | Cerrar evidencias pendientes; conservar este contrato |
| Usuarios | Registro, sesión, logout y `UserAdmin` | Reutilizar sesión en la futura API privada |
| Carrito | Servicios atómicos, resumen propio y web | Adaptadores DRF privados y equivalencia web/API |
| Pedidos | Checkout atómico, snapshots, lista/detalle propios y pruebas de RF-09 | Estado pagado, intentos de pago y enlace técnico al archivo comprado |
| Pagos | No hay modelo ni servicio de intentos; `Order.Status` solo tiene `pending_payment` | RF-07 y RF-08 |
| Licencias adquiridas | `LicenseType` describe el catálogo, no un derecho adquirido | Emisión y consulta de RF-10 |
| Archivos | Maestro privado sin URL pública, separado de previews | Vínculo estable de compra y entrega autorizada RF-11 |
| API privada | No existen endpoints privados de carrito, pago, pedido o licencia | RF-13 y RF-14 |
| Administración | `UserAdmin` registrado; Admin de catálogo y pedidos sin configurar | RF-15 |

Comprobaciones de esta revisión:

- Git estaba limpio en `70842ca` antes de estos cambios documentales.
- Ruff: `check --no-cache .` correcto y `format --no-cache --check .` con
  **114 archivos ya formateados**. `git diff --check` sin incidencias.
- `.env` no aparece entre los archivos versionados; no se leen sus valores.
- La captura aportada por el desarrollador del 27 de septiembre muestra
  PostgreSQL saludable, comprobaciones Django y migraciones correctas,
  **172 pruebas superadas en 21,04 s**, Ruff y dependencias correctos.
  Ese resultado procede de su ejecución: esta revisión documental no repite
  pytest ni certifica una nueva ejecución de la base de datos.

RF-09 continúa `Implementado`: las capturas y comprobación visual previstas
siguen pendientes. Su prueba de ausencia de efectos debe ampliarse a intentos
y derechos cuando existan. RF-05 tiene pendiente la equivalencia con RF-13.
La entrega debe completar también las evidencias antiguas y el manual de
instalación, no solo los siete requisitos restantes.

Se corrigen dos desajustes documentales sin declarar nueva verificación: la
cabecera de RF-01 se alinea con su índice y trazabilidad (`Aprobado`, cierre
pendiente); README refleja RF-04 como `Verificado`, ya registrado en sus
requisitos. El maestro privado ya existe, aunque la entrega aún no.

## 2. Alcance y decisiones propuestas

Los criterios completos están en [requisitos funcionales](/Users/alvaro/Workspace/Curso_Tokio/Proyecto_Final/Foleyra_Ecommerce/docs/requirements/functional-requirements.md).
RF-07, RF-08, RF-10, RF-11, RF-13 y RF-14 conservan el estado `Propuesto`.
RF-15 conserva sus siete criterios aprobados; sus cinco criterios adicionales
y la matriz concreta de permisos se presentan como propuestas. Redactar un
contrato no significa implementarlo ni aprobarlo automáticamente.

| Decisión propuesta | Motivo práctico |
|---|---|
| Pago simulado separado del checkout | Crear el pedido no debe cobrar ni depender del carrito posterior |
| Clave por intento, unicidad y transacción | Repeticiones o peticiones simultáneas no deben duplicar aprobaciones |
| Rechazo mantiene el pedido pendiente | Permite reintentar sin perder el pedido ni su historia |
| Emisión de un derecho por línea dentro de la aprobación | Evita pago confirmado con una emisión parcial |
| Regularización explícita de datos anteriores | Los GET no crean derechos ni adivinan asociaciones históricas |
| Referencia estable y clave privada capturada para la entrega | Un SKU mutable o reemplazar el maestro no debe cambiar el archivo comprado |
| Sesión y CSRF para API privada | Reutiliza la identidad existente y evita añadir otro sistema de credenciales |
| Consulta privada de ofertas comprables | Permite obtener `offer_id` sin cambiar la API pública ni necesitar Admin |
| Historia en solo lectura desde Admin | Evita cambiar estados, precios o permisos desde formularios genéricos |

Estas son decisiones de diseño propuestas para cerrar huecos reales del flujo.
Los nombres de modelos nuevos y su distribución exacta entre aplicaciones se
concretarán al implementar; no hay necesidad de crear todas las capas por adelantado.

Al llegar a RF-10 se amplía el servicio de aprobación de RF-07 para emitir
licencias en la misma transacción. RF-10/11 también amplían checkout para
capturar referencias de entrega. RF-11 añade rechazo de compras o aprobaciones
sin maestro preparado. Se actualizarán entonces los contratos y pruebas de
RF-06/07: estas ampliaciones aún no describen su comportamiento actual.

Fuera del MVP: pasarela real, tarjetas, webhooks, reembolsos, suscripciones,
DRM, CDN, ZIP, contratos PDF, nuevos sistemas de tokens y un backoffice propio.

## 3. Secuencia por hitos, sin fecha artificial

El orden indicado por el desarrollador se conserva:

**RF-07 → RF-08 → RF-10 → RF-11 → RF-13 → RF-14 → RF-15.**

Las versiones objetivo existentes son etiquetas de alcance; no alteran esta
secuencia. El 1 de octubre deja de ser objetivo de entrega. El calendario
anterior de agosto/septiembre también queda sustituido. No se fija otra fecha
hasta disponer de progreso observado y estimación del trabajo restante.

| Hito | Resultado que permite cerrarlo |
|---|---|
| 1 · RF-07 | Aprobar un pago simulado propio sin duplicación ni efectos parciales |
| 2 · RF-08 | Rechazar y reintentar conservando historial y estado correcto |
| 3 · RF-10 | Emitir derechos atómicamente, regularizar datos previos y consultarlos |
| 4 · RF-11 | Descargar el maestro correcto con autorización y conservación histórica |
| 5 · RF-13 | Usar el carrito por API con sesión, CSRF y reglas compartidas |
| 6 · RF-14 | Completar el flujo privado por API con los mismos resultados de negocio |
| 7 · RF-15 | Administrar catálogo y consultar historia con permisos definidos |
| 8 · Consolidación | Regresión completa, recorrido manual, evidencias, instalación limpia y documentación coherente |

Cada hito requiere criterios comprobados, revisión del diff y puerta de calidad
aplicable. La congelación funcional comienza al cerrar el alcance acordado,
antes de consolidación. Desde ahí se corrigen defectos y se prepara la entrega.
No se añaden funcionalidades para compensar haber movido la fecha.

Trabajar un criterio por sesión permite observar el avance sin convertir toda
la especificación en una tarea diaria. Para prácticas y entrevista junior, la
señal útil es poder explicar una decisión, demostrarla con una prueba y seguir
la petición hasta PostgreSQL; el número de criterios terminados por día aporta
menos información sobre la comprensión.

## 4. Análisis de seis preguntas o de dos

Antes de escribir la prueba, leer el criterio, localizar su recorrido y mirar
el código relacionado. Clasificar por comportamiento completo observable, no
por encontrar una función parecida.

### A. Falta comportamiento: seis preguntas

1. **¿Qué pide exactamente?** La regla y sus límites en una frase.
2. **¿Cuáles son las precondiciones?** Usuario, propiedad, estados y datos previos.
3. **¿Cuál es la acción?** Una petición o una operación concreta.
4. **¿Cuál es el resultado observable?** Respuesta, datos visibles y cambios
   persistidos, incluidos los que no deben ocurrir.
5. **¿Qué componentes participan?** Ruta, autenticación, vista, formulario o
   serializer, servicio o selector, modelos/ORM y presentación, solo si aplican.
6. **¿Cuál es el recorrido vertical?** Desde la acción hasta la respuesta,
   indicando dónde se autoriza, consulta, modifica o revierte.

Después: escribir y ejecutar la prueba, confirmar un RED por comportamiento
faltante, implementar el mínimo y comprobar GREEN. Un import roto, una URL de
prueba equivocada o PostgreSQL detenido no demuestran el incumplimiento del criterio.

### B. El comportamiento completo ya existe: dos preguntas

1. **Precondiciones:** datos mínimos que distinguen un resultado correcto de uno
   que podría pasar por casualidad.
2. **Recorrido:** componentes existentes que cumplen la regla y punto donde se
   observará el resultado.

Después: escribir o ampliar la prueba y ejecutarla. Si pasa desde el principio,
comprobar que ejercita realmente el criterio y registrar **cobertura de
comportamiento preexistente**. No romper código para fabricar RED ni modificar
componentes que ya cumplen. Si falla por un defecto real, volver al análisis
completo de la parte faltante.

Reducir preguntas no elimina la acción ni los `assert`: ambos siguen siendo
imprescindibles dentro de la prueba. Escribir una prueba es implementar código
de pruebas; ejecutarla con pytest es comprobarlo. El código de producción solo
cambia cuando falta comportamiento o existe un defecto.

### Clasificación inicial tras inspeccionar el código

| Criterios | Clasificación razonada |
|---|---|
| RF-07 y RF-08 | Requieren comportamiento nuevo; una vez construido el servicio, algunos errores o repeticiones podrán necesitar solo ampliar cobertura |
| RF-10 | No existe el derecho adquirido ni su emisión/consulta; requiere implementación |
| RF-11 | Requiere entrega y asociación histórica; CA-RF11-05 reutiliza protección de almacenamiento ya probada, pero hay que revisar cada superficie nueva |
| RF-13 y RF-14 | Servicios/selectores reutilizables, pero endpoints privados ausentes: ningún criterio HTTP completo está resuelto hoy |
| CA-RF15-01 | Candidato a solo prueba sobre acceso nativo existente; concretar roles y rutas y ejecutar antes de concluir |
| CA-RF15-05 y CA-RF15-07 | Candidatos a pruebas de comportamiento nativo después de registrar/configurar los modelos correspondientes |
| Resto de RF-15 | Necesita registro, permisos o presentación; CA03 reutiliza disponibilidad existente, pero falta la operación administrativa |

La clasificación se reevalúa al llegar a cada criterio: la implementación de uno
puede cubrir otro. Si una prueba existente ya demuestra todo el criterio, se
reutiliza su trazabilidad y se ejecuta; no se duplica solo para aumentar el contador.

## 5. Recorridos de referencia para orientar las preguntas

Son mapas de responsabilidades propuestos, no instrucciones para implementarlos
todos ahora. Los datos previos se preparan antes de iniciar cada recorrido.

### RF-07 · Aprobar un pago simulado

1. Con sesión y pedido propio pendiente, el cliente envía el formulario del detalle.
2. El navegador envía POST a la acción; Django resuelve URL y comprueba CSRF/autenticación.
3. La vista valida los campos admitidos y pasa usuario, ID, resultado y clave al servicio.
4. El servicio resuelve y bloquea el pedido propio, comprueba estado e idempotencia.
5. Modelos/ORM persisten intento y transición en una transacción PostgreSQL.
6. La vista redirige; el GET del detalle muestra estado y resultado sin repetir el pago.

### RF-08 · Rechazar y reintentar

1. El cliente envía un rechazo simulado desde el pedido pendiente.
2. Ruta, seguridad y vista siguen el mismo camino de RF-07.
3. El servicio registra el intento fallido y mantiene el pedido pendiente.
4. La respuesta redirige al detalle, que muestra el intento y la opción de reintento.
5. Reintentar es otro POST con clave nueva; el mismo servicio decide la transición.
6. Una aprobación posterior conserva el intento fallido y no puede ser revertida por un replay.

### RF-10 · Emitir y consultar una licencia adquirida

1. La emisión sucede al aprobar el pago: el servicio crea un derecho por línea
   dentro de la transacción, antes de confirmar su éxito.
2. Posteriormente, el cliente solicita `/licenses/` o el detalle de un derecho.
3. Django resuelve la ruta y comprueba la sesión; la vista pasa identidad e ID al selector.
4. El selector consulta solo derechos propios y sus datos históricos relacionados.
5. La vista entrega datos permitidos a la plantilla y devuelve HTML 200, o el error previsto.
6. Consultar nunca emite derechos; los pagos antiguos se regularizan por operación explícita.

### RF-11 · Descargar

1. La compra ya tiene derecho activo y vínculo revisado al maestro privado.
2. El cliente sigue el enlace protegido o escribe su URL; el navegador envía GET.
3. La vista exige sesión y consulta el derecho con su propietario y pedido pagado.
4. El componente de entrega resuelve la clave capturada de esa compra y abre el almacenamiento privado.
5. Devuelve los bytes como adjunto con cabeceras privadas, o el 404 controlado.
6. No publica la clave ni modifica pedido, derecho o carrito al entregar el archivo.

### RF-13 · Carrito por API

1. El consumidor obtiene una sesión mediante RF-04 y el token CSRF para escribir.
2. Envía la petición al endpoint privado; DRF autentica, comprueba permisos y valida la entrada.
3. La vista llama al selector de resumen o al servicio de añadir/eliminar según la operación.
4. El ORM consulta o modifica únicamente el carrito del usuario; las restricciones evitan duplicados.
5. El serializer representa campos permitidos; la vista devuelve JSON y el código definido.
6. Las reglas de disponibilidad, precio y pertenencia son las mismas que en la web.

### RF-14 · Compra y consultas por API

1. El consumidor con sesión envía checkout; DRF valida permisos, CSRF y cuerpo.
2. La vista llama al servicio existente de conversión y devuelve el pedido pendiente en JSON.
3. En otra petición solicita pago; el servicio compartido confirma intento, pedido y derechos atómicamente.
4. Para consultar, las vistas llaman a selectores propios; serializers muestran la historia sin modificarla.
5. Para descargar, se aplica la autorización de RF-11 y se devuelve el archivo binario; los errores son JSON.
6. La diferencia frente a la web está en la representación HTTP, no en las reglas de compra.

### RF-15 · Administración

1. Un operador con cuenta staff accede a `/admin/`; Django comprueba sesión y permisos de modelo.
2. Abre una pantalla autorizada de catálogo o historia.
3. En catálogo, el formulario valida una operación permitida y el ORM la persiste respetando restricciones.
4. El Admin registra el cambio y muestra el resultado; las consultas públicas posteriores reflejan la activación.
5. En pedidos, pagos y derechos se muestran datos en lectura, sin permitir cambiar estados mediante POST manipulado.
6. Los listados cargan sus relaciones de forma acotada y no presentan claves privadas del almacenamiento.

## 6. Cierre de un criterio y del MVP

Para cada criterio registrar: identificador, nombre/ruta de la prueba,
resultado real, componentes que lo cumplen y límites de cobertura. Los nombres
de pruebas y nuevos archivos se elegirán al desarrollarlo, no se inventa su existencia aquí.

Usar primero la prueba objetivo y luego la regresión apropiada. En concurrencia,
comprobar transacciones reales con conexiones PostgreSQL independientes; en
privacidad, contrastar dos propietarios; en N+1, evaluar las relaciones con uno
y varios elementos; en ausencia de efectos, comparar registros y valores antes
y después. Preparar fixtures fuera del tramo donde se miden consultas.

Al cerrar un hito aplicar RNF-11, revisar el recorrido manual, actualizar
evidencias y versionar cuando se solicite. La consolidación final incluye
instalación limpia, datos de demostración ficticios, revisión de permisos,
archivos privados y equivalencia web/API, además de documentación e historial
coherentes. Una suite verde es necesaria, pero no acredita por sí sola todo el MVP.

Siguiente unidad de trabajo: revisar el contrato propuesto de RF-07 y comenzar
por un solo criterio aprobado. Esta revisión no implementa esos requisitos,
no genera migraciones y no realiza commits ni publicación remota.


---

## Criterios completos en orden de implementación

### RF-07 — Simular un pago aprobado de forma independiente

#### Metadatos y alcance

- Actor: cliente autenticado. Prioridad: Must. Versión objetivo: v0.5.0.
- Estado: `Propuesto`; contrato redactado el 2026-09-27, pendiente de aprobación.
- Dependencias: RF-04, RF-06 y RF-09; RNF-01 a RNF-05, RNF-08, RNF-10 a RNF-13.
- Objetivo: aprobar un pago simulado de un pedido existente, sin volver a crear
  el pedido ni consumir el carrito actual. No se utilizan tarjetas, pasarelas,
  credenciales financieras, cobros reales ni webhooks.

#### Contrato propuesto

`POST /orders/{order_id}/payments/simulate/` recibe `result=approved` y una
`idempotency_key` UUID. Son los únicos campos de negocio admitidos; el
formulario también incluye `csrfmiddlewaretoken`, que valida Django. El formulario aparece en el detalle propio pendiente e
indica claramente que es una simulación. Generar la clave del formulario no
escribe datos de negocio. RF-08 añadirá `result=failed` a la misma operación.

Éxito: 302 al detalle propio, mensaje de pago simulado aprobado y estado `paid`.
GET sobre la operación: 405. POST sin CSRF: 403. Anónimo con CSRF válido: 302 al
login con `next` al detalle propio solicitado. Pedido ajeno o inexistente: 404
uniforme. Entrada ausente, inválida o campos manipulables no admitidos: 400.
Pedido ya pagado con otra clave o reutilización incompatible de clave: 409.

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

#### Criterios de aceptación propuestos

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

#### Orden test-first y evidencias previstas

01–03: acceso y formulario; 04–05: transición e integridad histórica;
06–07: idempotencia y concurrencia; 08–09: rollback y validación. El dominio de
pago todavía no existe: no se clasifican estos criterios completos como
«solo pruebas». Reutilizar autenticación o selectores no implementa el pago.

Pruebas de servicio/transacción y web; evidencia prevista en `docs/evidence/RF-07/`.
No hay ejecución ni evidencia nueva de este requisito en esta revisión.

### RF-08 — Simular un pago fallido y reintentarlo

#### Metadatos y contrato propuesto

- Actor: cliente autenticado. Prioridad: Must. Versión: v0.5.0.
- Estado: `Propuesto`. Dependencias: RF-07 y sus RNF, RF-06 y RF-09.
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

#### Criterios de aceptación propuestos

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

#### Orden y preparación

01–02: rechazo sin efectos indebidos; 03–04: replay y reintento; 05–06:
historial y estado final; 07–08: seguridad, concurrencia y rollback.
Las garantías heredadas de RF-07 son candidatas a regresión una vez implementado
RF-07, no comportamientos ya verificados hoy. Evidencia prevista: `docs/evidence/RF-08/`.

### RF-10 — Consultar las licencias propias

#### Metadatos y alcance

- Actor: cliente autenticado. Prioridad: Must. Versión: v0.6.0.
- Estado: `Propuesto`. Dependencias: RF-06 a RF-09; RNF-01 a RNF-06,
  RNF-08 y RNF-10 a RNF-13.
- Una licencia adquirida es un derecho asociado a una línea pagada; no es el
  modelo de catálogo `LicenseType`. Conserva propietario a través del pedido,
  identificador, línea, fecha de emisión y estado `active`.
- Los datos visibles proceden de `OrderItem`: producto, SKU, licencia y versión
  de términos. El MVP identifica la versión; no genera contratos PDF ni permite
  transferencias, suscripciones o revocaciones desde la interfaz del cliente.

#### Contrato e integración propuestos

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

#### Criterios de aceptación propuestos

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
- CA-RF10-06: dado un derecho propio, cuando se abre su detalle, entonces
  muestra los datos históricos y el enlace al pedido propio, sin sustituirlos
  por modificaciones del catálogo ni publicar rutas del maestro.
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

#### Orden y evidencias previstas

11: referencia técnica; 01–03: emisión transaccional; 10: datos anteriores;
04–08: consulta privada y navegación; 09: regresión y rendimiento.
Crear datos y consultar derechos son responsabilidades distintas aunque se
cierren en este requisito. Pruebas previstas de modelos, servicios y vistas;
evidencias en `docs/evidence/RF-10/`. No existen aún estos modelos ni interfaces.

### RF-11 — Descargar un archivo autorizado

#### Metadatos y alcance

- Actor: cliente autenticado con derecho adquirido. Prioridad: Must. Versión: v0.6.0.
- Estado: `Propuesto`. Dependencias: RF-06 a RF-10 y separación de maestros ya
  existente; RNF-01 a RNF-06, RNF-08 y RNF-10 a RNF-13.
- `GET /licenses/{license_id}/download/` entrega el archivo como adjunto mediante
  streaming, después de validar propietario, derecho activo, línea y pedido pagado.
- Una descarga autorizada es la decisión de acceso sobre un derecho persistido;
  no requiere crear un token, permiso nuevo o registro de descarga por cada GET.
  No se ofrecen enlaces públicos, firmados ni permanentes a almacenamiento en el MVP.
- Se permiten descargas repetidas del mismo archivo mientras exista el derecho.
  DRM, ZIP, conversión de audio, CDN y límites comerciales de descargas quedan fuera.

#### Identidad del archivo y política de entrega propuestas

Además de la referencia estable introducida en RF-10, la nueva línea de pedido
captura la clave interna del maestro en el almacenamiento privado. Esta clave
no se acepta desde el cliente, no es una URL y nunca se expone en HTML, JSON,
contextos de plantillas, errores ni logs. Las representaciones seleccionan los
campos permitidos y no incluyen objetos que expongan la clave. Reemplazar el maestro del catálogo produce otra clave y debe
conservar el objeto referenciado por compras anteriores. No se añade un gestor
de versiones: la aplicación y el Admin de RF-15 comparten una política que
escribe un objeto nuevo y no borra ni sobrescribe claves de compras anteriores.

«Maestro preparado» significa clave privada configurada, objeto existente y
asociación inequívoca con la compra; no basta una cadena no vacía.

Al activar RF-11, el checkout debe rechazar con 409 una oferta cuyo maestro no
esté preparado para capturarse. El servicio de pago debe rechazar un pedido
pendiente sin maestro preparado con 409, sin crear una aprobación.
Se amplían las pruebas y la documentación de RF-06/07 para estos dos guardas;
no se cambian los precios ni snapshots originales. Una pérdida operativa posterior
del archivo devuelve un error controlado de descarga, nunca otro archivo.

Para compras antiguas sin clave se exige una asociación explícita y revisada
con el archivo correcto. No se adivina por SKU, por nombre ni por el maestro
actual. Mientras falte esa asociación, la descarga devuelve 404 genérico y el
detalle propio informa de indisponibilidad. La regularización solo modifica el
vínculo técnico autorizado, conserva los datos históricos y es idempotente.

Anónimo: 302 al login con `next` interno. Licencia ajena, inexistente, inactiva,
pedido no pagado o archivo ausente: 404 genérico sin información interna.
Métodos no admitidos: 405. Una respuesta exitosa es 200 con
`Content-Disposition: attachment`, nombre seguro derivado de datos públicos y
`Cache-Control: private, no-store`; no permite elegir rutas mediante parámetros.

#### Criterios de aceptación propuestos

- CA-RF11-01: dada una compra propia pagada y un derecho activo con archivo
  preparado, cuando se solicita la descarga, entonces recibe 200 y los bytes
  del maestro correcto como adjunto, con cabeceras privadas y nombre seguro.
- CA-RF11-02: dado un visitante anónimo, cuando solicita la descarga, entonces
  se redirige al login con `next` interno y no recibe bytes privados.
- CA-RF11-03: dado un identificador ajeno/inexistente, derecho inactivo o pedido
  no pagado, cuando se solicita la descarga, entonces recibe 404 sin bytes ni
  detalles que revelen la existencia de una compra ajena.
- CA-RF11-04: dado un maestro ausente o una línea antigua sin asociación segura,
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
  indicado, sin modificar propiedad, precios o términos; repetirlo no cambia
  el resultado y un mapeo inexistente o ambiguo se rechaza sin asociación.
- CA-RF11-09: dado un derecho válido, cuando se repite la descarga o se usa un
  método no admitido, entonces el GET autorizado mantiene los mismos derechos
  y datos de negocio y el método no admitido responde 405 sin escritura.
- CA-RF11-10: dado el detalle de una licencia propia preparada, cuando se abre,
  entonces ofrece un enlace de descarga autenticada; la autorización se vuelve
  a comprobar en el servidor aunque el cliente escriba la URL directamente.

#### Orden y pruebas previstas

05: regresión de almacenamiento existente; 06–08: identidad de entrega y
preparación de compras; 01–04: entrega y permisos; 09–10: ausencia de efectos y
navegación. Se amplía CA-RF09-09 para los modelos de pago y derechos ya creados.
Las pruebas usan archivos temporales controlados y consumen `streaming_content`
para verificar los bytes. No se leen ni copian maestros reales como fixtures.
Evidencia prevista: `docs/evidence/RF-11/`.

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
  licencias, entonces obtiene solo derechos propios y datos históricos; ajeno
  e inexistente responden el mismo 404 y ningún GET emite derechos.
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
