# RF-11 — Preparación y captura del maestro: avance parcial

Revisión: **2026-10-22**. RF-11 conserva el estado **Aprobado** con implementación
parcial. Esta evidencia no cierra el requisito: la ruta y el enlace de descarga
todavía no existen y la validación manual completa queda pendiente.

## Recorrido conectado con el código

1. Antes de la compra, `set_product_master_audio` recibe `uploaded_file`, guarda
   una clave privada nueva, valida el archivo y registra su preparación. El
   servicio sirve para primera carga y sustitución; aún no tiene interfaz Admin.
2. El comprador autenticado selecciona una oferta y la añade al carrito.
3. `POST /orders/create/` llega a `create_order`, que llama a
   `create_order_from_cart(owner=request.user)`. El servidor resuelve la
   preparación a partir del maestro del producto; no acepta una clave del cliente.
4. El checkout rechaza una clave sin preparación o un archivo inexistente con
   `MasterNotPrepared`. La vista responde 409, sin pedido parcial ni vaciado.
   Si puede continuar, cada `OrderItem` captura la preparación correspondiente.
5. `POST /orders/{order_id}/payments/simulate/` llega a `simulate_payment` y
   `approve_simulated_payment`. Una nueva aprobación comprueba la preparación
   capturada por cada línea y su archivo antes de crear el intento, pasar a
   `PAID` o emitir derechos. Rechaza con 409 sin efectos parciales. Los replays
   se resuelven antes de esa comprobación, conservando la idempotencia existente.
6. Mis licencias permite consultar derechos y condiciones históricas. El paso
   siguiente, solicitar y recibir el archivo autorizado, continúa pendiente.

## Datos y almacenamiento

- `MasterAudioPreparation` conserva `storage_key` única, SHA-256, tamaño,
  formato, frecuencia, profundidad y fecha de creación. Sus restricciones
  exigen formato admitido, tamaño positivo, al menos 48 kHz y al menos 24 bits.
- `validate_master_audio` inspecciona WAV/BWF, FLAC y AIFF soportados y todos
  los bytes, sin convertir, normalizar ni remuestrear. Extensión y MIME no
  acreditan el contenido. SHA-256 identifica bytes, incluidos metadatos; no
  certifica calidad sonora ni resolución de origen.
- `prepare_master_audio` reutiliza la validación y la evidencia persistida.
  Repetir el mismo objeto es idempotente; otra evidencia bajo esa clave se
  rechaza. No restaura físicamente bytes que alguien haya sobrescrito.
- `set_product_master_audio` bloquea el producto, escribe otra clave y conserva
  los objetos anteriores. Ante un fallo tras el guardado intenta borrar el
  archivo nuevo y la transacción revierte los cambios de base de datos.
- `OrderItem.master_preparation` es una FK con `PROTECT`. Permite nulo para
  líneas anteriores y no inventa correspondencias. El checkout nuevo la captura
  antes del pago. Una sustitución del catálogo conserva el vínculo y el archivo
  original en los escenarios comprobados.
- PostgreSQL conserva referencias; los archivos están en almacenamiento privado
  en disco. Base de datos y archivos requieren conservación y respaldo conjuntos.

Migraciones del incremento: `catalog.0004_masteraudiopreparation`,
`catalog.0005_alter_masteraudiopreparation_prepared_at` y
`orders.0010_orderitem_master_preparation`.

## Matriz incremental de criterios

| Criterio | Estado en este incremento | Evidencia y trabajo restante |
|---|---|---|
| CA05 · Privacidad | Parcial | Catálogo con campos permitidos; pruebas de HTML/contextos, API y acceso directo a medios. Revisar las nuevas superficies de entrega. |
| CA11 · Calidad | Parcial integrado | Validación y preparación implementadas y probadas; checkout/pago consumen la preparación persistida. Falta reutilizarla en la asociación de compras antiguas y completar el recorrido. |
| CA06 · Histórico | Parcial | Captura en checkout, conservación de línea y bytes tras sustituir el maestro. Falta comprobar la descarga histórica y los demás cambios del catálogo en ese recorrido. |
| CA07 · Checkout/pago | Parcial | Rechazos por ausencia de preparación o archivo implementados; pruebas HTTP de producto sin maestro y pérdida del archivo antes de checkout/pago. Faltan casos específicos indicados abajo. |
| CA08 · Compras antiguas | Pendiente | Falta asociación explícita y revisada del maestro. Los servicios RF-10 regularizan derechos/documentación, no este vínculo. |
| CA01 · Entrega | Pendiente | Ruta, streaming de bytes completos, nombre público seguro, extensión real y cabeceras privadas. |
| CA02 · Anónimo | Pendiente | La prueba mantiene `xfail(strict=True)`; la ruta aún no redirige al login. |
| CA03 · Autorización | Pendiente | Comprobar propiedad, derecho activo y pedido pagado en la ruta de descarga. |
| CA04 · Error de entrega | Pendiente | 404 genérico para archivo ausente/ inválido o asociación no segura. |
| CA09 · Repetición/métodos | Pendiente | GET sin escrituras y repetible; métodos no permitidos con 405. |
| CA10 · Enlace | Pendiente | Enlace autenticado desde el detalle del derecho y aviso de indisponibilidad. |
| CA12 · Varias líneas | Pendiente | Descargas individuales del maestro correcto por línea, sin ZIP ni mezcla. |

## Pruebas principales existentes

- `apps/catalog/tests/test_services.py`: validación real de formatos, mínimos,
  codificación, truncamiento, propiedades declaradas, SHA-256 y conservación de
  bytes; preparación persistida/idempotente y carga/sustitución del maestro.
- `test_create_order_from_cart_captures_prepared_master_for_order_item`:
  preparación capturada en PostgreSQL antes de pagar y sin emitir derechos.
- `test_order_item_preserves_captured_master_after_catalog_replacement`:
  producto con otra clave, línea histórica conservada y ambos archivos exactos.
- `test_checkout_without_master_file_returns_conflict_and_preserves_cart`:
  409, sin pedido parcial y carrito conservado.
- `test_checkout_with_missing_stored_master_returns_conflict_without_changes`:
  permanece la preparación pero desaparecen los bytes; 409 sin cambios de negocio.
- `test_payment_with_missing_captured_master_returns_conflict_without_changes`:
  pérdida posterior al checkout; 409, pedido pendiente, sin intento ni derechos.
- Las pruebas del catálogo cubren no exposición de claves, nombres y raíz
  privada, separación de previews y acceso directo con DEBUG activado/desactivado.

La función compartida `prepare_product_master` genera un WAV real y llama al
servicio. La fixture de pedidos aísla el almacenamiento en una carpeta temporal.
Las ofertas válidas se preparan por defecto; `with_master=False` conserva los
escenarios que construyen expresamente su maestro o deben carecer de él. Las
líneas históricas creadas directamente no se asocian automáticamente.

## Resultados y límites

Los resultados actuales ejecutados se registran en la
[puerta de calidad del 2026-10-22](quality-gate-2026-10-22.md). Los 62 casos de
catálogo aportados anteriormente por Álvaro y las regresiones de pedidos son
evidencia de sus ejecuciones concretas, no sustituyen esta revisión completa.

Pendientes inmediatos: incorporar y ejecutar la prueba del pago sin preparación
capturada (borrador guardado, todavía incompleto), probar el pago después de sustituir
el maestro del catálogo y cubrir una clave con archivo pero sin preparación.
Después: asociación revisada de compras antiguas y descarga autorizada.

Las comprobaciones actuales consultan la preparación y la existencia del
archivo; no vuelven a decodificar ni recalculan el hash en checkout/pago.
Se conserva la política de claves nuevas y de no sobrescritura. No se han
probado todos los errores de almacenamiento ni todos los fallos de base de
datos posteriores a preparar el archivo. Las pruebas usan archivos controlados;
procedencia, escucha, instalación limpia, interfaz Admin y validación manual
de extremo a extremo siguen pendientes. Esta revisión no acredita despliegue.
