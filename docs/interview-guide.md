# Guía técnica para aprendizaje y entrevista

## Idea central

El valor defendible de esta fase no está en memorizar comandos ni en ocultar el
uso de IA. Está en comprender las decisiones, reproducir las verificaciones y
explicar la relación causa-efecto entre Django, el usuario intercambiable, las
migraciones y PostgreSQL.

## Presentación breve de la fase

> Preparé un monolito modular con Django 5.2.17 sobre Python 3.12.13. Desde el
> inicio configuré PostgreSQL 18.6 mediante Docker Compose y evité SQLite para
> que el esquema inicial se validara en el mismo motor elegido para el
> proyecto. Antes de ejecutar la primera migración definí un usuario propio
> basado en `AbstractUser` y configuré `AUTH_USER_MODEL`. Después generé y
> revisé la migración, la apliqué, comprobé que existe `users_user` y que no se
> creó `auth_user`, y cerré el incremento con pruebas, análisis estático,
> documentación y commits pequeños.

Usa esta presentación solo después de poder justificar cada frase con el
código o una verificación.

## Secuencia técnica que debes poder explicar

1. El entorno fijó Python y las dependencias mediante `.python-version` y
   pip-tools.
2. Docker Compose levantó PostgreSQL con un volumen persistente y un health
   check.
3. `config/settings.py` cargó las variables privadas desde `.env`.
4. `DATABASES["default"]` se configuró con
   `django.db.backends.postgresql`, sin alternativa SQLite.
5. Se creó `apps.users.User` heredando de `AbstractUser`.
6. Se configuró `AUTH_USER_MODEL = "users.User"`.
7. Solo entonces se ejecutó `makemigrations users`.
8. Se revisó `migrate --plan` antes de ejecutar `migrate`.
9. Se verificaron el modelo resuelto, las tablas y la ausencia de migraciones
   pendientes.
10. Se ejecutaron pruebas y comprobaciones antes de cerrar los commits.

El orden es importante: las migraciones de autenticación y de otras
aplicaciones resuelven el modelo intercambiable de usuario. Cambiarlo después
de crear relaciones y tablas iniciales puede exigir reconstruir dependencias,
datos y claves foráneas.

## Decisiones técnicas y respuestas

### ¿Por qué PostgreSQL desde la primera migración?

Porque evita validar el modelo sobre un motor y desplegarlo sobre otro. SQLite
y PostgreSQL difieren en tipos, restricciones, concurrencia y comportamiento
SQL. Usar PostgreSQL desde el inicio reduce diferencias de entorno y cumple el
ADR-002.

### ¿Por qué un usuario personalizado tan pronto?

Django permite sustituir el usuario mediante `AUTH_USER_MODEL`, pero recomienda
que el modelo exista en la migración inicial de su aplicación. Definirlo antes
de la primera migración evita una sustitución posterior costosa y mantiene
estables las futuras relaciones.

### ¿Por qué heredar de `AbstractUser`?

Porque conserva el comportamiento probado de autenticación de Django —nombre
de usuario, contraseña, permisos, grupos y administración— y permite ampliar el
modelo más adelante. `AbstractBaseUser` daría más control, pero obligaría a
implementar manager, campos y administración sin que exista un requisito que
lo justifique.

### ¿Por qué el modelo no tiene campos adicionales?

Porque todavía no hay un requisito aprobado que los necesite. Crear campos por
anticipado aumenta migraciones, decisiones de validación y deuda accidental.
El modelo ya es extensible sin inventar dominio.

### ¿Cómo se protegen los secretos?

`.env` contiene los valores locales y está ignorado por Git. `.env.example`
solo documenta nombres y marcadores. La configuración lee las variables en
tiempo de ejecución y ni las pruebas ni las capturas deben mostrar sus valores.

### ¿Qué diferencia hay entre `makemigrations` y `migrate`?

`makemigrations` compara los modelos con el estado conocido y genera archivos
de migración versionables. `migrate` calcula sus dependencias y aplica esas
operaciones a la base de datos. Revisar `migrate --plan` permite ver el orden
antes de modificar el esquema.

### ¿Cómo demuestras que no se usó SQLite?

La configuración declara el backend PostgreSQL, el contenedor informa la
versión 18.6, las pruebas con base de datos pasan contra PostgreSQL y la
introspección muestra `users_user`. Además, no existe un archivo SQLite dentro
del proyecto.

### ¿Por qué DRF está instalado si aún no hay endpoints?

Forma parte del stack aprobado, pero esta fase solo prepara la base técnica.
No crear endpoints evita mezclar infraestructura con requisitos del catálogo
que todavía no están aprobados.

### ¿Qué aportan los commits pequeños?

Separan estructura, migración, prueba y documentación. Esto facilita revisar,
explicar o revertir una decisión y permite relacionar cada resultado con una
verificación concreta.

## Cómo explicar el uso de IA

Una respuesta transparente y profesional sería:

> Utilicé ChatGPT Codex para ejecutar la inicialización bajo un prompt con
> alcance y restricciones explícitas. Conservé el prompt y los commits como
> trazabilidad. Antes de presentar esta fase reproduje las comprobaciones y
> estudié cada archivo. Para los siguientes incrementos usaré GitHub Copilot
> como asistente, pero separaré planificación, prueba, implementación y
> revisión, y no aceptaré cambios que no pueda explicar.

No afirmes que revisaste o reprodujiste algo hasta haberlo hecho. Tampoco es
necesario disculparse por usar una herramienta: explica qué controles aplicaste
y demuestra criterio propio.

## Ejercicio personal antes de continuar

### Lectura de código

Sin pedir explicaciones a Copilot, responde por escrito:

1. ¿Qué ruta sigue `manage.py` hasta cargar `config.settings`?
2. ¿Qué variables son obligatorias y cuáles tienen valor por defecto?
3. ¿Por qué el nombre de la tabla es `users_user`?
4. ¿Qué dependencia contiene `users.0001_initial` y por qué?
5. ¿Cómo sabe Django qué modelo debe registrar el Admin?
6. ¿Qué prueba accede a PostgreSQL y por qué necesita `django_db`?

### Reproducción

Ejecuta personalmente los comandos del inventario de evidencias. Para cada uno,
anota:

- qué valida;
- qué salida esperas;
- qué fallo detectaría;
- qué archivo revisarías si fallara.

### Revisión histórica

Usa `git show` sobre cada commit de la fase y explica qué propósito único tiene.
Comprueba también que ningún commit introdujo SQLite, secretos, dependencias o
catálogo.

## Señales de que ya puedes pasar a la siguiente fase

- Puedes explicar la secuencia completa sin leer este documento.
- Puedes reproducir todas las verificaciones y entender sus salidas.
- Reconoces dónde se configura PostgreSQL y el usuario personalizado.
- Puedes revisar una migración inicial y relacionarla con el modelo.
- Puedes explicar honestamente qué hizo la IA y qué validaste tú.
- El repositorio está limpio y las evidencias no contienen secretos.
- El siguiente requisito está aprobado y tiene criterios comprobables.

Hasta cumplir estas condiciones, pausar el código es una decisión técnica
correcta, no una pérdida de tiempo.

## Referencias oficiales

- [Personalización de autenticación en Django 5.2](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/)
- [Migraciones en Django 5.2](https://docs.djangoproject.com/en/5.2/topics/migrations/)
