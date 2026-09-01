# Evidencia de puerta de calidad — RF-03 (2026-09-01)

## Criterios cubiertos

CA-RF03-01, CA-RF03-02, CA-RF03-03, CA-RF03-04, CA-RF03-05, CA-RF03-06 y
CA-RF03-07. Además, esta ejecución cubre RN-RF03-08 (`category`/`license`
inválidos responden 400) y la precedencia de FE-01 sobre FE-02, que no tienen
todavía un `CA-RF03-0X` numerado en `docs/requirements/functional-requirements.md`.

## Pruebas ejecutadas

Batería completa del proyecto mediante `.venv/bin/python -m pytest -q`,
incluidas todas las pruebas de `apps/catalog/tests/test_views.py` y
`apps/catalog/tests/test_selectors.py` asociadas a RF-03.

## Resultado de la suite

```
41 passed in 1.38s
```

## Controles de calidad

| Comprobación | Comando | Resultado |
|---|---|---|
| Sistema Django | `manage.py check --database default` | `System check identified no issues (0 silenced).` |
| Migraciones pendientes de generar | `manage.py makemigrations --check --dry-run` | `No changes detected` |
| Migraciones pendientes de aplicar | `manage.py migrate --check` | Sin salida (sin pendientes) |
| Suite de pruebas | `pytest -q` | `41 passed in 1.38s` |
| Lint | `ruff check .` | `All checks passed!` |
| Formato | `ruff format --check .` | `70 files already formatted` |
| Dependencias | `pip check` | `No broken requirements found.` |
| Espacios en el diff | `git diff --check` | Sin salida (sin errores) |
| Estado del árbol de trabajo | `git status --short` | 8 archivos modificados, sin migraciones ni archivos nuevos de código |

## Comprobación manual

No se registró ninguna comprobación manual (captura de navegador u observación
visual) en este cierre.

## Migraciones incluidas

Ninguna. `makemigrations --check --dry-run` no detectó cambios de modelo.

## Limitaciones conocidas

- No existe evidencia formal individual para CA-RF03-01 a CA-RF03-06 (solo
  CA-RF03-07 cuenta con `docs/evidence/RF-03/CA-RF03-07.md`); esta puerta de
  calidad acredita la suite completa, pero no sustituye la evidencia
  específica por criterio.
- La validación de `category`/`license` inválidos (RN-RF03-08) y la
  precedencia FE-01/FE-02 no tienen un `CA-RF03-0X` numerado asignado
  (ver nota en `docs/requirements/functional-requirements.md`).
- Ninguna prueba combina un filtro `license` activo con ofertas de precio
  distinto para comprobar que `Desde` conserva el mínimo global (D-RF03-05).
- El conteo acotado de consultas no se probó combinando búsqueda, filtros,
  orden y paginación a la vez.

## Referencia del requisito

`docs/requirements/functional-requirements.md`, sección RF-03.

## Futura referencia de commit

Pendiente. Ningún cambio de este cierre se ha confirmado todavía con
`git commit`.

## Estado resultante

RF-03 permanece en `Implementado`. No se declara `Verificado` porque la
cadena de trazabilidad (`Evidencia → Versión Git`) sigue incompleta: falta
evidencia individual por criterio y no existe todavía un commit que registre
este incremento.
