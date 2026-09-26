# Puerta de calidad automatizada — RF-09 (2026-09-26)

## Cambio revisado

Listado y detalle privados de pedidos, navegación autenticada y pruebas de los
criterios CA-RF09-01 a CA-RF09-11. Se revisaron el diff y las plantillas nuevas.
La preparación de modelos, `created_at`, migraciones y selectores ya existía.

La revisión final detectó que el listado todavía no mostraba la fecha ni el
acceso al detalle previstos en el flujo principal aprobado. Se añadieron ambos
campos, manteniendo los marcadores de pedido utilizados por las pruebas de
orden y aislamiento.

## RED y GREEN del ajuste final

Comando:

```bash
.venv/bin/python -m pytest apps/orders/tests/test_views.py::test_authenticated_user_sees_own_order_fields_in_list -q
```

- RED: `1 failed in 0.84s`; el HTML no contenía la fecha en el elemento `time`.
- GREEN: `1 passed in 0.66s`; fecha y enlace al detalle presentes tras el cambio.

También se corrigieron las erratas `fileds` y `changues` en dos nombres de prueba
para mantener una trazabilidad legible, sin alterar sus casos de negocio.

## Puerta completa ejecutada

Los siguientes comandos se ejecutaron en secuencia con `set -e`, contra el
PostgreSQL local configurado, después del ajuste de plantilla:

```bash
set -e
.venv/bin/python manage.py check --database default
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py migrate --check
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pip check
git diff --check
```

| Comprobación | Resultado observado |
|---|---|
| Django y base de datos | `System check identified no issues (0 silenced).` |
| Migraciones por generar | `No changes detected` |
| Migraciones por aplicar | Sin salida, código 0 |
| Suite completa | `172 passed in 19.50s` |
| Ruff | `All checks passed!` |
| Formato | `112 files already formatted` |
| Dependencias | `No broken requirements found.` |
| Espacios del diff | Sin salida, código 0 |

`pip check` informó además de que su directorio de caché no era escribible en
el entorno de ejecución; deshabilitó la caché y finalizó correctamente. No se
cambiaron permisos, dependencias ni configuración para ocultar ese aviso.

## Límites de la evidencia

- La suite acredita el comportamiento automatizado; no se ha realizado en este
  cierre una comprobación visual manual ni se han generado capturas del navegador.
- CA-RF09-09 cubre los modelos existentes de pedidos y carrito. La cobertura de
  pagos, licencias adquiridas y descargas autorizadas deberá añadirse cuando
  existan esos modelos.
- CA-RF09-10 mide el GET y su renderizado, excluyendo la preparación de datos;
  verifica igualdad de recuentos y un máximo de cuatro consultas, no un tiempo
  máximo de respuesta ni la escalabilidad de todo el sistema.
- La prueba de 404 genérico se ejecuta con `DEBUG=False`.
- No se añadieron migraciones, API privada, pagos ni descarga de archivos.

RF-09 queda `Implementado`, con la verificación visual pendiente. La evidencia
pertenece al mismo commit que las rutas, vistas, plantillas y pruebas del
incremento; véase el [índice de RF-09](README.md).
