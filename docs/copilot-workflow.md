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

## Situación actual: cerrar y aprender

No es necesario escribir más código ahora. Antes del primer requisito de
catálogo:

1. realizar las capturas indicadas en `docs/evidence/phase-01/README.md`;
2. leer `config/settings.py`, `apps/users/models.py` y la migración inicial;
3. explicar en voz alta por qué `AUTH_USER_MODEL` debía preceder a `migrate`;
4. localizar en PostgreSQL la tabla `users_user` y confirmar que `auth_user` no
   existe;
5. repetir las pruebas y comprender qué comprueba cada una;
6. revisar los cuatro commits de implementación de la fase 01;
7. no iniciar el catálogo hasta aprobar el requisito y sus criterios.

## Ciclo para cada incremento futuro

### 1. Planificar sin editar

En Copilot Chat:

```text
/plan-requirement requirementId=RF-XX
```

Revisar personalmente el alcance, los riesgos, la migración propuesta y el
plan de pruebas. Corregir primero el requisito si faltan decisiones.

### 2. Crear una prueba y observar Red

```text
/write-tests requirementId=RF-XX criterion=CA-RFXX-XX
```

Leer la prueba línea por línea. Ejecutarla y confirmar que falla por la ausencia
del comportamiento, no por un error de sintaxis, entorno o datos.

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
