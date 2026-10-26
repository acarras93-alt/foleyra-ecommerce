# RF-11 — Preparación y descarga autorizada del maestro: verificado

Revisión: **2026-10-26**. RF-11 está **Verificado** en el alcance aprobado del
MVP. Se validan la preparación técnica del maestro, su captura en cada línea
comprada, las guardas de checkout y pago y la descarga individual desde la
licencia adquirida.

## Alcance verificado

CA-RF11-08 fue retirado del MVP el 2026-10-22, sin renumerar los criterios.
Quedan activos CA-RF11-01 a CA-RF11-07 y CA-RF11-09 a CA-RF11-12. No se
asocian automáticamente los pedidos de desarrollo antiguos que carecen de una
referencia segura al maestro.

El recorrido comprobado es:

1. `set_product_master_audio` guarda una clave privada nueva, inspecciona el
   archivo real y registra su preparación.
2. El checkout captura esa preparación en `OrderItem.master_preparation` para
   cada línea; no acepta del navegador una ruta o clave de almacenamiento.
3. El pago comprueba la preparación capturada y la existencia del archivo antes
   de aprobar una compra nueva y emitir sus derechos.
4. «Mis licencias» presenta el enlace de descarga para un derecho activo de un
   pedido pagado.
5. `GET /licenses/<license_id>/download/` vuelve a comprobar la propiedad,
   el pago, el derecho y la preparación, y transmite como adjunto los bytes del
   maestro histórico de esa línea.

La sustitución del maestro del catálogo crea otra clave y conserva el objeto
capturado por las compras anteriores. Cada línea tiene una descarga propia;
no se ofrece un ZIP ni se combinan maestros.

## Validación y almacenamiento

- Se admiten WAV/BWF, FLAC y AIFF que cumplan los mínimos de 48 kHz y 24 bits.
  La validación inspecciona el contenido y las propiedades reales; no convierte
  ni remuestrea el audio.
- `MasterAudioPreparation` conserva clave interna, SHA-256, tamaño, formato,
  frecuencia, profundidad y fecha de preparación.
- PostgreSQL conserva las relaciones y el archivo se guarda en `private_media/`.
  El maestro no tiene URL pública. Deben conservarse juntos la base de datos y
  el almacenamiento privado.
- Una descarga válida responde 200 con los bytes completos, tipo de contenido,
  nombre y extensión acordes con la compra, `Content-Disposition: attachment`
  y `Cache-Control: private, no-store`.
- El visitante anónimo se redirige al login. Licencias ajenas o inexistentes,
  pedidos no pagados, preparación ausente y archivos desaparecidos responden
  con error controlado sin entregar bytes privados. Las peticiones GET
  repetidas no cambian el pedido, el pago ni la licencia; otros métodos
  responden 405.

## Evidencia automatizada

Las pruebas usan archivos temporales; no copian la biblioteca comercial al
repositorio.

- `apps/catalog/tests/test_services.py`: formatos admitidos, mínimos, contenido
  truncado o mal declarado, integridad, huella SHA-256, preparación idempotente,
  claves nuevas y conservación del objeto anterior al sustituirlo.
- `apps/catalog/tests/test_views.py`: el acceso anónimo a la ruta de descarga
  redirige al login; las URL públicas de medios no permiten obtener el maestro.
- `apps/orders/tests/test_services.py` y `test_views.py`: captura en checkout,
  rechazos de checkout/pago sin maestro, pago tras sustituir el maestro, acceso
  propio, rechazo de licencias ajenas/inexistentes y pedidos sin pagar, errores
  por vínculo o archivo ausente, respuesta y cabeceras de WAV/FLAC/AIFF,
  repetición sin cambios, métodos no permitidos y descargas distintas por cada
  línea de un pedido con varios productos.

La última regresión completa registrada obtuvo **434 pruebas aprobadas** y
superó Django checks, comprobaciones de migraciones, Ruff y dependencias. El
resultado está en la [puerta de calidad registrada el 2026-10-26](../RF-15/quality-gate-2026-10-26.md).

## Evidencia manual y límites

El recorrido manual de entrega se documenta con capturas en el material final:
inicio de sesión, catálogo, carrito, pedido, pago simulado, licencia y descarga
del archivo esperado. El pago no realiza un cargo real. Las capturas visuales
complementan la regresión automatizada y acreditan la experiencia observada con
el producto de demostración preparado.

La verificación corresponde al MVP y al entorno local documentado. No acredita
un despliegue en producción, la procedencia de todos los sonidos de una
biblioteca, la carga del maestro desde Django Admin, DRM, descargas masivas ni
la redistribución de archivos de audio. Para reproducir el recorrido se prepara
localmente un maestro autorizado mediante el servicio descrito en el [manual de
instalación](../../installation.md).

La puerta del **2026-10-22** conserva los resultados de una fase anterior y
parcial de RF-11; se mantiene como registro histórico. La evidencia de cierre
actual es la revisión de esta página junto con la regresión completa del
2026-10-26 y las capturas del recorrido manual.
