# Flujo personal de trabajo con GitHub Copilot

## Objetivo

Usar Copilot para acelerar análisis, pruebas, implementación y revisión sin
delegar la comprensión ni la decisión final.

## Preparación única en Visual Studio Code

1. Abrir como carpeta raíz `Foleyra_Ecommerce`, no su directorio padre.
2. Seleccionar el intérprete `.venv/bin/python`.
3. Comprobar que las instrucciones personalizadas del repositorio están
   habilitadas.
4. Abrir Copilot Chat y verificar en las referencias de una respuesta que se
   ha cargado `.github/copilot-instructions.md`.
5. Confirmar que los prompts del directorio `.github/prompts` aparecen al
   escribir `/` en el chat.

Las instrucciones globales se cargan automáticamente. Los archivos
`.instructions.md` se aplican cuando coinciden con los archivos de trabajo. Los
prompts se invocan manualmente para mantener cada responsabilidad separada.

## Situación actual al 2026-10-14

Catálogo, API pública, autenticación, carrito y consulta de pedidos ya tienen
implementación. RF-07/08/10 tienen cierre documentado: emisión, consulta privada,
condiciones capturadas, referencias estables, regularización y bloqueo de recompra.
Continúan RF-11, RF-13, RF-14 y RF-15. Sus contratos,
pendientes y resultados se consultan en requisitos y evidencias; una nueva
redacción no implica aprobación ni ejecución.

Hasta finalizar el proyecto, aplicar la
[premisa de trabajo del 2026-10-07](requirements/mvp-implementation-plan.md#4-premisa-de-trabajo-hasta-el-cierre-del-proyecto):

- leer un criterio en una o dos frases y revisar primero la cobertura existente;
- reutilizar o ampliar pruebas suficientes y crear una nueva solo cuando falte;
- delegar la escritura mecánica de la prueba y revisar preparación, operación
  y fallos que detectan las comprobaciones;
- concentrar el aprendizaje en la pieza nueva de la implementación;
- cerrar con prueba específica, regresión pertinente y nota breve de cobertura.

Las seis preguntas son una guía de apoyo para dudas y riesgos, no una obligación
de análisis exhaustivo. El ciclo Red-Green y el Green inicial justificado para
comportamiento existente se mantienen. La puerta completa corresponde al cierre
del requisito o versión, sin impedir controles adicionales por un riesgo concreto.

Se trabaja un criterio por vez. Los flujos antiguos del catálogo se conservan
como referencia de aquella fase; su calendario ya no rige la entrega actual.

## Ciclo para cada incremento futuro

### 1. Planificar sin editar

En Copilot Chat:

```text
/plan-requirement requirementId=RF-XX
```

Revisar personalmente el alcance, los riesgos, la migración propuesta y el
plan de pruebas. Corregir primero el requisito si faltan decisiones.

### 2. Crear una prueba y comprobar el estado real

```text
/write-tests requirementId=RF-XX criterion=CA-RFXX-XX
```

Leer la prueba línea por línea. Ejecutarla y confirmar que falla por la ausencia
del comportamiento, no por un error de sintaxis, entorno o datos. Si pasa
porque el comportamiento ya existe, revisar la suficiencia de la prueba y
registrar ese Green inicial; no se requiere un cambio de producción ni un
fallo artificial. Si una prueba existente ya es suficiente, se reutiliza.

No crear un commit mientras el repositorio quede deliberadamente en rojo.

### 3. Implementar el mínimo y obtener Green

```text
/implement-requirement requirementId=RF-XX criterion=CA-RFXX-XX
```

Rechazar cambios adicionales, abstracciones prematuras y cualquier dependencia
no aprobada. Si surge una migración no prevista, detener el paso y revisarla por
separado.

### 4. Separar la revisión de la implementación

Abrir una conversación nueva o cambiar a modo de consulta:

```text
/review-change scope=working-tree
```

La revisión de Copilot no sustituye la revisión personal. Comprobar cada
hallazgo contra el código y descartar los que no sean reproducibles.

### 5. Verificación humana

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
git status --short
```

Ejecutar solo comandos comprendidos y añadir verificaciones específicas del
requisito. Revisar también el diff completo y los archivos no rastreados.

### 6. Documentar y crear un commit pequeño

Actualizar requisito, log técnico y evidencias cuando corresponda. El commit
debe representar una sola unidad funcional, incluir sus pruebas y dejar todas
las verificaciones en verde.

Copilot puede proponer el mensaje, pero no debe crear el commit sin autorización.

## Regla personal de aceptación

No aceptar un cambio hasta poder responder afirmativamente:

- ¿Puedo explicar cada archivo modificado?
- ¿Sé qué prueba fallaba antes y por qué ahora pasa?
- ¿He revisado permisos, datos privados y casos límite?
- ¿He comprobado que no aparece SQLite ni una dependencia nueva?
- ¿La migración, si existe, es necesaria y está revisada?
- ¿El diff contiene únicamente el alcance aprobado?
- ¿Podría reproducir y defender la decisión sin abrir el chat de Copilot?

## Referencias oficiales

- [Instrucciones personalizadas de repositorio](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide)
- [Prompt files en Visual Studio Code](https://code.visualstudio.com/docs/agent-customization/prompt-files)
