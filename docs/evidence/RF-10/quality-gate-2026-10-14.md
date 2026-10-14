# RF-10 — Puerta de calidad del 2026-10-14

## Procedencia de los resultados

Álvaro aportó una captura de la puerta completa con **314 passed in 40.75s**,
Django sin incidencias, modelos sin cambios pendientes, migraciones comprobadas,
Ruff correcto, 123 archivos formateados y dependencias compatibles. Sobre esa
base solicitó actualizar la documentación, crear el commit y pasar RF-10 a
Verificado.

La revisión de cierre añadió ocho casos que faltaban en la matriz: siete
rechazos parametrizados de correspondencia histórica CA15 y una comprobación
de consultas constantes del detalle CA09. No modificó reglas de producción.
Las pruebas nuevas pasaron en su primera ejecución; no se atribuye un Red de
implementación a esta ampliación.

Codex ejecutó después la puerta sobre los archivos guardados del repositorio,
con Python de `.venv`, Django y la base PostgreSQL de pruebas. Esta ejecución
final es distinta a la comprobación anterior de correcciones solo en memoria.

## Resultado final ejecutado

| Comando | Resultado |
|---|---|
| `.venv/bin/python manage.py check --database default` | Sin incidencias, código 0 |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | `No changes detected`, código 0, sin advertencias de conexión |
| `.venv/bin/python manage.py migrate --check` | Código 0, sin migraciones pendientes |
| `.venv/bin/python -m pytest -q -p no:cacheprovider` | **322 passed in 45.49s**, código 0 |
| `.venv/bin/ruff check --no-cache .` | `All checks passed!` |
| `.venv/bin/ruff format --no-cache --check .` | `123 files already formatted` |
| `.venv/bin/python -m pip check` | `No broken requirements found`, código 0 |
| `git diff --check` | Sin incidencias |
| `.venv/bin/python manage.py showmigrations catalog orders` | Aplicadas hasta `catalog.0003` y `orders.0009` |

Deshabilitar las cachés de bytecode, pytest y Ruff durante la revisión no cambia
las comprobaciones ni sus aserciones. pip avisó de que su caché local no era
escribible y la deshabilitó; la comprobación de dependencias terminó correctamente.
No se aplicaron migraciones ni se modificaron dependencias.

## Incidencias de preparación resueltas antes del cierre

La regresión anterior reprodujo 49 fallos y 265 pruebas satisfactorias. Las
preparaciones de compras válidas aún omitían condiciones, identidades declaradas
y referencias técnicas exigidas por CA12/16. También se restauraron los datos
originales del helper de servicios, que una prueba histórica seguía esperando.

Se completaron las ofertas de prueba y se añadió `create_payable_order_item`
únicamente a los casos que debían permitir pagar. Las compras antiguas, campos
incompletos y referencias sin resolver conservaron su preparación negativa.
El pedido de tres líneas pasó a sumar 31,30 EUR, manteniendo sus precios
individuales. No se desactivaron políticas ni se relajaron las comprobaciones.

## Alcance del cierre

RF-10 queda Verificado para la [matriz CA01–CA16](README.md), con los límites
allí documentados. La operación administrativa se ofrece mediante servicios
internos controlados; no se presenta como una interfaz Admin ya implementada.
No se acredita validación visual manual, autenticidad jurídica de documentos,
instalación limpia, entrega del maestro, API privada ni despliegue.

El commit incluye únicamente los archivos del incremento RF-10 y su documentación.
No incorpora `.env`, credenciales, bases, medios privados ni capturas temporales.
No se publica el commit en un remoto como parte de esta operación.
