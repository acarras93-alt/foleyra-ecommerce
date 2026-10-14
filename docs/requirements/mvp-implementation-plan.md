# Plan de cierre del MVP y metodología por criterio

Fecha de revisión: 2026-10-14. Base anterior: `be94cb1`, más el incremento de
cierre de RF-10. RF-10 queda `Verificado` en el alcance automatizado descrito en
[las evidencias](../evidence/RF-10/README.md). El siguiente requisito es RF-11.

## 1. Estado comprobado antes de planificar

La base permite descubrir productos, gestionar una cuenta y un carrito privado,
crear un pedido, consultar su historia y simular pagos aprobados, rechazos y
reintentos. Ya emite permisos al aprobar el pago y ofrece listado/detalle
privados con condiciones capturadas, regularización y prevención de recompra.
RF-10 tiene cierre documentado. Todavía no entrega el maestro comprado: el
trabajo funcional inmediato sigue en RF-11.

| Área | Código observado | Qué falta para el recorrido completo |
|---|---|---|
| Catálogo y API pública | Modelos, selectores, web, previews y endpoints públicos | Cerrar evidencias pendientes; conservar este contrato |
| Usuarios | Registro, sesión, logout y `UserAdmin` | Reutilizar sesión en la futura API privada |
| Carrito | Servicios atómicos, resumen propio y web | Adaptadores DRF privados y equivalencia web/API |
| Pedidos | Checkout atómico, condiciones completas, referencias a producto/tipo y consultas propias | Preparación histórica de entrega RF-11; evidencias pendientes de RF-06/09 |
| Pagos | Intentos, replay, emisión atómica, bloqueo de recompra y rechazo de condiciones/identidades incompletas | Preparación de entrega RF-11; conservar RF-07/08 |
| Licencias adquiridas | RF-10 verificado: emisión, consultas, regularización, recompra, versionado y condiciones | Conservar las garantías al integrar entrega y futura API privada |
| Archivos | Maestro privado sin URL pública, separado de previews | Vínculo estable de compra y entrega autorizada RF-11 |
| API privada | No existen endpoints privados de carrito, pago, pedido o licencia | RF-13 y RF-14 |
| Administración | `UserAdmin` registrado; Admin de catálogo y pedidos sin configurar | RF-15 |

Comprobaciones y límites de esta revisión:

- Se contrastan modelos, servicios, rutas, pruebas y documentos de evidencia.
  Se conservan los cambios locales del desarrollador y se preparan para publicar
  por solicitud expresa, sin adelantar funcionalidades pendientes.
- RF-07 consta como `Verificado` el 2026-10-02 y RF-08 el 2026-10-03.
  La [puerta de calidad de RF-08](../evidence/RF-08/quality-gate-2026-10-03.md)
  registra **219 pruebas superadas**, controles Django, Ruff y dependencias.
  Son resultados de esa ejecución, no una nueva certificación de este árbol.
- RF-06 y RF-09 continúan `Implementado`, con evidencias de cierre pendientes.
  RF-10 ya comprueba que consultar listado/detalle no altera pedidos, intentos,
  carrito ni permisos; RF-08 verifica la lectura propia del historial de intentos.
- RF-05 mantiene pendiente la equivalencia con RF-13. API privada, descargas y
  Admin de catálogo no están implementados. RF-10 queda verificado; sus resultados
  y límites se consultan en la evidencia enlazada arriba.
- La revisión de septiembre en `70842ca` era anterior a RF-07/08. Sus resultados
  de 172 pruebas y 114 archivos formateados son históricos, no la línea base
  vigente para planificar este cierre.

La entrega debe completar las evidencias pendientes y el manual de instalación.
El almacenamiento privado ya existe; eso no acredita todavía una descarga
autorizada ni una demo con audios reales.

## 2. Alcance y decisiones propuestas

Los criterios completos están en [requisitos funcionales](functional-requirements.md).
RF-07, RF-08 y RF-10 están `Verificado`. RF-11, RF-13 y RF-14 conservan
el estado `Propuesto`; priorizarlos no aprueba todos sus contratos técnicos.
RF-15 conserva sus siete criterios aprobados; sus cinco criterios adicionales
y la matriz concreta de permisos se presentan como propuestas. Redactar un
contrato no significa implementarlo ni aprobarlo automáticamente.

| Decisión existente o propuesta | Motivo práctico |
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

Las tres primeras decisiones forman parte de RF-07/08 y la emisión por línea
ya usa `orders.LicenseGrant`. Las restantes conservan el estado de su RF:
RF-10 captura y valida condiciones y exige nueva versión ante cambios;
`source_product` no sustituye el vínculo histórico al archivo de RF-11.

RF-10 ya amplía la aprobación de RF-07 con emisión en la misma transacción y
el checkout con condiciones y referencia al producto. Capturar el archivo
histórico de entrega y rechazar compras/aprobaciones sin maestro preparado
siguen pendientes de RF-11. No se atribuye esa protección al código actual.

Fuera del MVP: pasarela real, tarjetas, webhooks, reembolsos, suscripciones,
DRM, CDN, ZIP, contratos PDF, nuevos sistemas de tokens y un backoffice propio.

## 3. Secuencia por hitos y cierre funcional inmediato

La secuencia de referencia del alcance completo se conserva:

**RF-07 → RF-08 → RF-10 → RF-11 → RF-13 → RF-14 → RF-15.**

Las versiones objetivo existentes son etiquetas de alcance; no alteran esta
secuencia. El 1 de octubre deja de ser objetivo de entrega. El calendario
anterior de agosto/septiembre también queda sustituido. El objetivo expresado
el 2026-10-04 es cerrar esta fase en una semana, dos como máximo; orienta el foco
y la reserva de tiempo para validación, sin garantizar el alcance completo en
ese plazo ni convertirlo en una fecha de entrega certificada.

El trabajo inmediato se organiza como **Cierre funcional del MVP**:

1. **Implementación del flujo de adquisición y entrega:** RF-10 verificado;
   continuar con RF-11 y un primer sonido real preparado.
2. **Validación de extremo a extremo con productos sonoros reales:** recorrido
   web integrado con una muestra pequeña, evidencias y corrección de defectos.

Esta validación se realiza al terminar RF-11, antes de iniciar RF-13/14.
RF-13, RF-14 y RF-15 permanecen pendientes dentro del alcance documental.
Cerrar el recorrido web no equivale a declarar verificados esos requisitos ni
a entregar v1.0.0. Si se decide reducir el alcance de la primera entrega, deberá
quedar registrado antes de presentarla como el MVP completo.

La propuesta de priorizar **RF-10 → RF-11 → RF-15 → validación y entrega**, dejando
RF-13/14 como evolutivos, continúa pendiente de confirmar con el instructor.
Esta revisión no reduce el alcance aprobado ni cambia requisitos a opcionales.
El margen orientativo discutido para 6–7 horas diarias es de 3–4 semanas con
ese alcance reducido, o 4–6 semanas manteniendo la API privada completa. Es una
estimación revisable, no una fecha comprometida ni evidencia de finalización.

| Hito | Resultado que permite cerrarlo |
|---|---|
| 1 · RF-07 | Aprobar un pago simulado propio sin duplicación ni efectos parciales |
| 2 · RF-08 | Rechazar y reintentar conservando historial y estado correcto |
| 3 · RF-10 | Registrar permisos atómicamente, conservar condiciones trazables y consultar compras propias |
| 4 · RF-11 | Descargar el maestro correcto con autorización y conservación histórica |
| 5 · RF-13 | Usar el carrito por API con sesión, CSRF y reglas compartidas |
| 6 · RF-14 | Completar el flujo privado por API con los mismos resultados de negocio |
| 7 · RF-15 | Administrar catálogo y consultar historia con permisos definidos |
| 8 · Consolidación | Regresión completa, validación con audios reales, evidencias, instalación limpia y documentación coherente |

Cada hito requiere criterios comprobados, revisión del diff y puerta de calidad
aplicable. La congelación funcional comienza al cerrar el alcance acordado,
antes de consolidación. Desde ahí se corrigen defectos y se prepara la entrega.
No se añaden funcionalidades para compensar haber movido la fecha.

Trabajar un criterio por sesión permite observar el avance sin convertir toda
la especificación en una tarea diaria. Para prácticas y entrevista junior, la
señal útil es poder explicar una decisión, demostrarla con una prueba y seguir
la petición hasta PostgreSQL; el número de criterios terminados por día aporta
menos información sobre la comprensión.

## 4. Premisa de trabajo hasta el cierre del proyecto

Premisa acordada por el desarrollador el **2026-10-07**, vigente hasta finalizar
el proyecto. El objetivo es terminar el curso y preparar las prácticas con
comprensión suficiente, sin convertir cada criterio en una investigación
exhaustiva. Esta pauta sustituye la obligación de repetir un análisis extenso
por criterio; no cambia contratos funcionales ni estados de verificación.

1. **Un criterio cada vez.** Extraer sus comportamientos en una o dos frases.
   El asistente propone esa lectura y señala únicamente las ambigüedades que
   cambian lo que debe hacer la aplicación.
2. **Revisar primero la cobertura existente.** Identificar qué prueba ya
   demuestra el criterio, cuál ampliar y cuándo hace falta una nueva. Reutilizar
   los escenarios suficientes en vez de reconstruirlos o duplicarlos por capa.
3. **Delegar la escritura mecánica.** El asistente puede redactar la prueba
   completa. El desarrollador revisa qué prepara, qué operación ejecuta y qué
   fallo detectan sus comprobaciones. No necesita dominar toda la infraestructura
   de concurrencia para continuar; las garantías exigidas siguen comprobándose.
4. **Concentrar el aprendizaje en la implementación.** Seguir la conexión entre
   vista, servicio, modelos y base de datos, profundizando en la pieza nueva.
   En RF-10 es esencial entender por qué la transacción incluye el intento de
   pago aprobado, el cambio de estado del pedido y la emisión de permisos.
5. **Cerrar con evidencia suficiente.** Ejecutar la prueba específica y la
   regresión correspondiente y registrar una nota breve de cobertura. Ampliar
   solo si aparece un riesgo concreto o falta una parte explícita del criterio.
   La puerta completa de RNF-11 se aplica al cierre del requisito o versión;
   un riesgo concreto puede justificar adelantar comprobaciones.

Red por comportamiento faltante, Green inicial justificado cuando ya existe,
PostgreSQL, revisión humana y controles de seguridad e integridad se mantienen.
La delegación de la redacción de pruebas no autoriza implementación masiva ni
avance automático al siguiente criterio. Los resultados se registran después
de ejecutar las comprobaciones; una prueba redactada no constituye evidencia.

Antes de escribir la prueba, leer el criterio, localizar su recorrido y mirar
solo el código relacionado. Clasificar por comportamiento completo observable,
no por encontrar una función parecida. Las preguntas siguientes son una guía
de apoyo: se utilizan cuando una duda o un riesgo lo requiera, sin exigir seis
respuestas desarrolladas para cada comportamiento nuevo.

### A. Falta comportamiento: guía de apoyo para dudas o riesgos

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
componentes que ya cumplen. Si falla por un defecto real, analizar la parte
faltante con la profundidad que requiera su riesgo.

Reducir preguntas no elimina la acción ni los `assert`: ambos siguen siendo
imprescindibles dentro de la prueba. Escribir una prueba es implementar código
de pruebas; ejecutarla con pytest es comprobarlo. El código de producción solo
cambia cuando falta comportamiento o existe un defecto.

### Clasificación de referencia tras inspeccionar el código el 2026-10-04

Esta tabla conserva la línea base de esa revisión. Antes de cada criterio se
consulta el código y las pruebas actuales; los avances posteriores no se
deducen del estado histórico de esta tabla.

| Criterios | Clasificación razonada |
|---|---|
| RF-07 y RF-08 | Comportamiento implementado y evidencias de verificación existentes; reutilizar cobertura y ampliar solo las garantías afectadas por RF-10/11 |
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

### RF-10 · Registrar y consultar permisos de uso con condiciones trazables

Orientación acordada el 2026-10-04. Los 16 criterios quedan documentados como
verificados el 2026-10-14 en `functional-requirements.md` y las evidencias de RF-10.

1. Antes de crear el pedido, el cliente puede consultar las condiciones de la oferta.
2. El checkout captura versión, texto completo, alcance, concedente y titular
   declarado junto con los datos históricos; la preparación incompleta impide la compra.
3. Al aprobar el pago se registra un permiso por línea en la misma transacción,
   usando las condiciones del pedido, aunque después cambie el catálogo.
4. El cliente abre «Mis licencias» (`/licenses/`) y el detalle de un permiso.
5. Django comprueba la sesión y el selector obtiene solo permisos propios;
   la plantilla muestra condiciones históricas y procedencia del pedido.
6. Consultar nunca emite permisos ni reconstruye condiciones desde el catálogo.
   Los pagos antiguos y su documentación se regularizan por operaciones explícitas
   con correspondencia revisada; los datos desconocidos se indican como tales.

Los permisos registrados no representan una transmisión de propiedad intelectual.
RF-10 no incorpora PDF, registro oficial de derechos ni control de usos posteriores;
la descarga privada continúa en RF-11.

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
instalación limpia, cuentas y compras de prueba con una muestra de audios reales,
revisión de permisos, archivos privados y equivalencia web/API según el alcance
implementado, además de documentación e historial coherentes. Una suite verde
es necesaria, pero no acredita por sí sola todo el MVP.

### Validación de extremo a extremo con productos sonoros reales

Esta actividad aplica RNF-12 y complementa RNF-06, RNF-08, RNF-10 y RNF-11.
Su estado inicial es **pendiente**; la documentación del protocolo no constituye
evidencia de ejecución.

#### Muestra y preparación

- Comenzar con un sonido durante RF-10/11 y usar hasta tres productos distintos
  para la validación integrada, con sus maestros y previews separados.
- Preparar las previews manualmente y registrar metadatos técnicos coherentes
  con los archivos. No se exige conversión, recorte ni extracción automática.
- Utilizar dos cuentas de prueba, condiciones completas y pagos simulados.
  Elegir audios propios o autorizados para el uso previsto en la demo.
- Trabajar con copias de los audios seleccionados y conservar la biblioteca
  original. No se introduce importación masiva ni clasificación de la colección.
- Documentar cómo preparar productos y archivos en el entorno local. La
  reproducción no debe depender de una ruta personal ni del acceso a toda la
  biblioteca. Las pruebas automáticas mantienen archivos temporales controlados;
  no usan maestros personales como fixtures ni requieren acceso a esa biblioteca.

#### Persistencia que debe observarse

PostgreSQL conserva metadatos, referencias de archivo y relaciones de negocio;
los bytes se guardan en el almacenamiento de archivos. En la configuración
local actual, `PreviewStorage` utiliza `BASE_DIR / "media"` y
`PrivateMasterStorage`, `BASE_DIR / "private_media"`; `upload_to` añade
`previews/` y `masters/`, respectivamente. Son ubicaciones de desarrollo,
no URLs públicas de descarga del maestro ni un requisito de infraestructura
de producción. Conservar solo la base de datos no conserva los audios.

Al implementar RF-10/11 se observará la cadena usuario → pedido → línea
histórica → permiso adquirido → referencia privada del maestro comprado.
La sesión identifica al solicitante; el servidor comprueba propiedad y estado
antes de abrir el archivo. El tipo de licencia del catálogo no sustituye al
permiso adquirido. Referencias históricas y campos nuevos siguen pendientes
de implementación, aunque ya estén descritos en los RF.

#### Protocolo y condiciones de cierre

| Comprobación | Resultado observable | Referencias |
|---|---|---|
| Explorar y escuchar antes de comprar | Preview reproducible y condiciones de la oferta consultables, sin acceso público al maestro | RF-02, CA-RF10-16, CA-RF11-05 |
| Crear un pedido y aprobar el pago simulado | Datos de compra capturados; permiso propio por línea pagada; un replay no duplica permisos | CA-RF10-01, CA-RF10-13 |
| Consultar el permiso | Condiciones históricas y procedencia del pedido visibles; GET sin escrituras | CA-RF10-06, CA-RF10-09 |
| Descargar como propietario | Adjunto con los bytes del maestro comprado; comparar tamaño y hash con la copia de referencia y comprobar reproducción | CA-RF11-01 |
| Solicitar la misma descarga como otro usuario y como anónimo | Denegación prevista por el contrato y ausencia de bytes privados | CA-RF11-02, CA-RF11-03 |
| Cambiar condiciones y maestro del catálogo mediante una operación permitida | La compra conserva condiciones y archivo originales, sin reconstruirlos desde el catálogo actual | CA-RF10-14, CA-RF11-06 |

Una escucha ayuda a validar la experiencia; no sustituye la comparación de bytes.
Los fallos de emisión, concurrencia y ausencia de archivo se verifican mediante
las pruebas controladas previstas en RF-10/11, sin destruir maestros de la demo
ni intentar certificar esas garantías solo con clics en el navegador.

Registrar en las evidencias de RF-10/11 una referencia al mismo recorrido:
versión o commit y cambios locales relevantes, productos/cuentas de prueba,
criterios ejercitados, resultado esperado y observado, comprobación de archivo
y defectos o límites pendientes. No publicar credenciales, claves privadas del
almacenamiento ni audios sin autorización; la revisión interna de referencias
no convierte esos valores en datos públicos de la aplicación.

La validación se cierra cuando el recorrido y las denegaciones cumplen el
contrato, las evidencias están registradas, se han corregido los defectos
bloqueantes y la regresión y puerta de calidad aplicables pasan. Cualquier paso
no ejecutado queda como pendiente. Su cierre no acredita API privada, Admin,
despliegue ni requisitos fuera del recorrido probado.

Siguiente unidad de trabajo: revisar el contrato de RF-11 y preparar un sonido
real como apoyo al aprendizaje. La reorganización de los archivos de pruebas
queda como tarea separada; no se mezcla con el cierre funcional de RF-10.
El commit de este cierre incorpora el código existente, la migración 0009,
las pruebas y la documentación; no implica publicación remota.
