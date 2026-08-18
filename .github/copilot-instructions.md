# Instrucciones de GitHub Copilot para Foleyra

## Contexto y fuentes de verdad

- Trabaja como asistente de un proyecto Django y Django REST Framework con
  PostgreSQL.
- Consulta antes de proponer cambios: `.python-version`, `requirements.in`,
  `requirements-dev.in`, `docs/technology-stack.md`, `docs/installation.md`,
  `docs/decisions/`, `docs/requirements/` y `docs/technical-log.md`.
- Si una petición contradice una fuente de verdad, señala la contradicción y
  detente antes de editar.
- No inventes requisitos, criterios de aceptación, versiones o evidencias.

## Restricciones obligatorias

- No añadas, elimines ni actualices dependencias sin autorización explícita.
- No configures ni utilices SQLite. Todas las pruebas de base de datos deben
  ejecutarse con PostgreSQL.
- No edites `.env`, no muestres sus valores y no incluyas secretos en código,
  pruebas, capturas o documentación.
- Conserva `AUTH_USER_MODEL = "users.User"`.
- Usa `settings.AUTH_USER_MODEL` en relaciones declarativas y
  `get_user_model()` cuando necesites resolver el modelo en tiempo de ejecución.
- Antes de crear o aplicar una migración, confirma el modelo de usuario activo,
  revisa el plan y solicita autorización si la migración no estaba aprobada.
- No ejecutes operaciones destructivas sobre bases de datos, volúmenes o Git.
- No implementes el catálogo hasta que el usuario abra expresamente un
  requisito aprobado con criterios de aceptación suficientes.

## Flujo de trabajo obligatorio

1. Empieza leyendo el requisito y comprobando `git status --short`.
2. Resume el alcance, lo que queda fuera y los archivos previstos.
3. Propón un plan de pruebas y verificaciones antes de editar.
4. Para reglas de negocio, crea primero la prueba y confirma que falla por el
   motivo esperado.
5. Implementa el cambio mínimo para cumplir el criterio aprobado.
6. Revisa el diff completo y evita reformateos o refactors ajenos al alcance.
7. Ejecuta las pruebas específicas y después la batería aplicable.
8. Informa de los comandos realmente ejecutados y de su resultado. Nunca
   afirmes que una prueba pasó si no se ejecutó.
9. No hagas commits sin solicitud explícita. Propón un mensaje de commit de una
   sola finalidad y deja el repositorio en estado válido.

## Arquitectura y estilo

- Mantén el monolito modular: configuración global en `config` y aplicaciones
  de negocio bajo `apps`.
- Web y API deben reutilizar las mismas reglas de negocio.
- Mantén el código y los identificadores en inglés; redacta documentación y
  explicaciones del proyecto en español.
- No añadas abstracciones anticipadas ni campos de modelo sin un requisito.
- Las migraciones deben ser generadas por Django, revisadas y trazables.

## Verificaciones base

Usa el entorno virtual del repositorio. Como mínimo, cuando sean aplicables:

```bash
.venv/bin/python manage.py check --database default
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py migrate --check
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pip check
git diff --check
```
