# RF-11 parcial — Puerta de calidad del 2026-10-22

## Procedencia y alcance

Revisión solicitada por Álvaro para actualizar la documentación y guardar el
incremento en Git antes de continuar. Base anterior: `09877c8`. Se comprueban
los archivos guardados del repositorio con Python de `.venv` y PostgreSQL.

Se deshabilitan bytecode y cachés de pytest/Ruff para la revisión. No se aplican
migraciones ni se modifican datos de demostración. Las pruebas crean su base
separada y utilizan almacenamiento temporal para los maestros.

## Resultados ejecutados

| Comprobación | Resultado |
|---|---|
| `.venv/bin/python -B -m pytest -p no:cacheprovider --tb=short -q` | 399 passed, 1 xfailed; 46,89 s |
| `.venv/bin/python -B manage.py check --database default` | Sin incidencias |
| `.venv/bin/python -B manage.py makemigrations --check --dry-run` | Sin cambios pendientes |
| `.venv/bin/python -B manage.py migrate --check` | Migraciones aplicadas |
| `.venv/bin/python -B manage.py showmigrations catalog orders` | Aplicadas hasta `catalog.0005` y `orders.0010` |
| `.venv/bin/ruff check --no-cache .` | **Pendiente: 3 incidencias** en el borrador descrito abajo |
| `.venv/bin/ruff format --no-cache --check .` | 128 archivos con formato correcto |
| `.venv/bin/python -B -m pip --disable-pip-version-check --no-cache-dir check` | Dependencias compatibles |
| `.venv/bin/python -B -m pip --disable-pip-version-check --no-cache-dir install --dry-run --require-hashes -r requirements-dev.txt` | Requisitos satisfechos en el entorno actual; sin instalación |
| Enlaces locales de los ocho documentos actualizados | Destinos existentes |
| `git diff --check` | Sin errores de espacios |

**La puerta no está completamente en verde.** Se conserva el borrador
`test_payment_without_captured_master_returns_conflict_without_changes` al
final de `apps/orders/tests/test_views.py`, sin completar código del autor.
Todavía no elimina el vínculo ni realiza la petición y las aserciones. Ruff
detecta la importación sin uso de `MasterAudioPreparation` y las variables
`order` y `master_file` sin usar. El resultado numérico de pytest no acredita
ese escenario: un borrador sin aserciones puede terminar correctamente.
Se guarda el incremento como trabajo en curso; completar esta prueba y repetir
Ruff y las regresiones afectadas es el siguiente paso.

## Dependencias

Se regeneran `requirements.txt` y `requirements-dev.txt` con pip-tools y
SHA-256, a partir de los `.in`. Se añade `soundfile==0.13.1` junto con
`cffi==2.1.1`, `numpy==2.5.4` y `pycparser==3.11`. Se conservan exactamente
las siete versiones previas del bloqueo de producción y las veinte del de
desarrollo. No se instalan ni actualizan paquetes del entorno.

La simulación de instalación utiliza paquetes ya instalados: comprueba que
los requisitos están satisfechos, pero no verifica una descarga nueva de
cada distribución ni sustituye una instalación limpia.

## Límites

RF-11 conserva `Aprobado` e implementación parcial. El fallo esperado estricto
de la descarga anónima no es una verificación del criterio: permanece porque
la ruta de descarga protegida todavía no existe. La matriz y los siguientes
pasos están en [el registro incremental](README.md).

Esta puerta no acredita revisión manual completa, instalación en una máquina
limpia, escucha/procedencia de audios reales, regularización del maestro de
compras antiguas, interfaz administrativa, descarga ni despliegue. Las pruebas
posteriores del pago sin vínculo y tras sustitución del catálogo siguen pendientes.
