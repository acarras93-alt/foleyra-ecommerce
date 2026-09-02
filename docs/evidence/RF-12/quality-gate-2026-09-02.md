# Evidencia de puerta de calidad — RF-12 (2026-09-02)

## Criterios cubiertos

CA-RF12-01, CA-RF12-02, CA-RF12-03, CA-RF12-04, CA-RF12-05, CA-RF12-06 y
CA-RF12-07. También se midió RN-RF12-06 como regresión de consultas sin N+1;
su resultado es Green preexistente y no acredita un ciclo RED-GREEN propio.

## Pruebas ejecutadas

| Alcance | Comando | Resultado |
|---|---|---|
| API de catálogo | `.venv/bin/python -m pytest -q apps/catalog/tests/test_api.py` | `43 passed in 2.49s` |
| Proyecto completo | `.venv/bin/python -m pytest -q` | `86 passed in 3.35s` |

## Controles de calidad

| Comprobación | Resultado |
|---|---|
| PostgreSQL | Contenedor `db` saludable |
| Sistema Django | `System check identified no issues (0 silenced).` |
| Migraciones por generar | `No changes detected` |
| Migraciones por aplicar | Sin salida, sin pendientes |
| Lint | `All checks passed!` |
| Formato | `75 files already formatted` |
| Dependencias | `No broken requirements found.` |
| Espacios en el diff | Sin salida, sin errores |

## Comprobación manual

- `GET /api/v1/catalog/products/`: `200 application/json`; `count` igual a 17,
  12 resultados en la primera página y `next` relativo a la página 2.
- `GET /api/v1/catalog/products/rf03-ambiente-01/`: `200 application/json`;
  metadatos públicos, una oferta pública y `preview_url` igual a `null`.

Las respuestas observadas se conservan en `api-catalogo-lista.json` y
`api-catalogo-detalle.json`.

## Migraciones incluidas

Ninguna. RF-12 no modifica modelos ni el esquema de PostgreSQL.

## Limitaciones conocidas

- Las API privadas y RF-04 a RF-11 permanecen fuera de alcance.
- La descarga autorizada del archivo maestro corresponde a RF-11 y no está
  implementada.
- La medición de RN-RF12-06 es una regresión Green preexistente.

## Trazabilidad

- Requisito: RF-12 en `docs/requirements/functional-requirements.md`.
- Pruebas: `apps/catalog/tests/test_api.py`.
- Evidencia: este documento y los snapshots JSON asociados.
- Commit: pendiente; no se creó ningún commit en este cierre.

## Estado resultante

RF-12 queda `Verificado` con las comprobaciones registradas en esta evidencia.