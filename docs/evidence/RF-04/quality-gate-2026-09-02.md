# Evidencia de puerta de calidad - RF-04 (2026-09-02)

## Criterios cubiertos

CA-RF04-01, CA-RF04-02, CA-RF04-03, CA-RF04-04, CA-RF04-05, CA-RF04-06,
CA-RF04-07, CA-RF04-08 y CA-RF04-09.

## Pruebas ejecutadas

| Alcance | Comando | Resultado |
|---|---|---|
| Vistas de usuarios | `.venv/bin/python -m pytest apps/users/tests/test_views.py -q` | `21 passed in 4.35s` |
| Proyecto completo | `.venv/bin/python -m pytest -q` | `107 passed in 7.31s` |

## Controles de calidad

| Comprobación | Resultado |
|---|---|
| Sistema Django | `System check identified no issues (0 silenced).` |
| Migraciones por generar | `No changes detected` |
| Migraciones por aplicar | Sin salida, sin pendientes |
| Lint | `All checks passed!` |
| Formato | `88 files already formatted` |
| Dependencias | `No broken requirements found.` |
| Espacios en el diff | Sin salida, sin errores |

## Evidencias visuales

- `registro-valido.png`: catálogo y control de cierre de sesión tras un registro
  válido.
- `login-y-logout.png`: catálogo anónimo con enlaces de acceso, tras completar
  login y logout mediante el formulario `POST` con CSRF.

## Migraciones incluidas

Ninguna. RF-04 no modifica el esquema y reutiliza `users.User` de
`apps/users/migrations/0001_initial.py`.

## Trazabilidad

- Requisito: RF-04 en `docs/requirements/functional-requirements.md`.
- Pruebas: `apps/users/tests/test_views.py` y
  `apps/users/tests/test_user_model.py`.
- Evidencia: este documento, `registro-valido.png` y `login-y-logout.png`.
- Commit: pendiente de crear; se asociará al incremento RF-04.

## Limitaciones conocidas

- La autenticación de la API privada se definirá en RF-13.
- Correo de activación o recuperación, MFA, autenticación social o sin
  contraseña y perfiles públicos permanecen fuera de alcance.
- Durante la captura, el servidor de desarrollo respondió 404 para
  `/static/css/site.css`; las imágenes acreditan el flujo funcional, pero se
  muestran sin los estilos de la aplicación. La resolución de estáticos no
  forma parte de RF-04.

## Estado resultante

La puerta de calidad está registrada y todos los criterios aprobados disponen
de cobertura acreditada. RF-04 queda `Verificado`; la referencia de commit se
completará cuando se cree.
