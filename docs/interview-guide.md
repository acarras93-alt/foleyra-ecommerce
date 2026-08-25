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

## Informe del catálogo v0.2.0

### Pasos realizados

1. Se definieron RF-01, RF-02, RF-03, RF-12 y RF-15 y se aprobaron.
2. Se creó `apps.catalog` con `Category`, `Product`, `LicenseType` y
   `ProductLicenseOffer`.
3. Se escribió una prueba de persistencia para demostrar que un producto puede
   tener ofertas con licencias y precios distintos.
4. La primera ejecución de esa prueba falló porque la tabla
   `catalog_category` todavía no existía. Fue un bloqueo de esquema, no un Red
   válido de la regla de negocio.
5. Se aprobó D-CAT-01, que descarta suscripciones, stock y descargas
   ilimitadas para el MVP.
6. Se revisó `catalog.0001_initial`, se confirmó su plan y se aplicó en
   PostgreSQL. La prueba focalizada pasó y la suite completa cerró con
   `7 passed`.

### Evaluación de la secuencia

Aprobar los requisitos funcionales antes de implementar fue necesario y
correcto, pero no fue suficiente. Los requisitos delimitan el comportamiento
esperado; las decisiones del catálogo cierran cómo se modela ese comportamiento.
Antes de crear modelos, pruebas de persistencia o migraciones debían estar
aprobadas las decisiones que esos elementos codifican.

En particular, `ProductLicenseOffer` separa producto, licencia y precio. Por
tanto, el modelo y la prueba de precios distintos dependen directamente de
D-CAT-02, además de apoyar D-CAT-01 y la regla RN-RF01-08. D-CAT-02 quedó
aprobada el 2026-08-25; la estructura existente fue creada antes, cuando aún
era una recomendación documentada. Por ello no debe presentarse como una
implementación test-first de esa decisión, ni como cumplimiento completo de
RF-01 o incremento terminado del catálogo.

La prueba actual es útil como prueba de modelo: verifica que dos ofertas
persistidas para el mismo producto conservan una licencia y precio propios.
No prueba todavía una compra, porque RF-06 no está aprobado ni existen pedidos.
Tampoco sustituye las pruebas de catálogo web, API, disponibilidad, seguridad,
paginación o rendimiento previstas por RF-01, RF-02, RF-03 y RF-12.

### Patrón obligatorio para un nuevo incremento

1. Identificar el RF y el criterio de aceptación exacto.
2. Confirmar que el RF está `Aprobado` y revisar ADR y RNF aplicables.
3. Aprobar primero las decisiones de dominio, datos, seguridad y contrato HTTP
   que el incremento vaya a codificar.
4. Escribir una prueba mínima trazable a ese criterio o decisión y ejecutarla.
   El Red solo es válido si falla por la ausencia del comportamiento, no por
   imports, configuración, tablas o PostgreSQL.
5. Implementar el cambio mínimo, generar y revisar la migración cuando sea
   necesaria, y aplicarla únicamente después de revisar su plan.
6. Ejecutar la prueba objetivo en Green, la regresión aplicable y la puerta de
   calidad.
7. Actualizar requisito, decisión, bitácora y evidencia con resultados reales.

### Conclusión defendible en entrevista

> Para el catálogo aprobamos primero los requisitos funcionales, pero aprendimos
> que eso no sustituye el cierre de las decisiones de dominio. La relación
> producto-licencia-precio que implementamos depende de D-CAT-02. Esa decisión
> quedó aprobada el 2026-08-25, pero el modelo y la migración la precedieron;
> por eso no los presento como un incremento test-first completo. La primera
> prueba falló porque faltaba el esquema, así que no la presento como un Red de
> negocio; después de revisar y aplicar la migración en PostgreSQL, la prueba
> pasó. En los siguientes incrementos usaré la cadena requisito aprobado,
> decisión aprobada, prueba Red válida, implementación, migración revisada,
> Green y evidencia. Esto evita que una recomendación de diseño se convierta
> prematuramente en una dependencia persistente.

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

### Respuestas verificadas: 2 y 4

**2. Variables obligatorias y valores por defecto.** `DJANGO_SECRET_KEY`,
`POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` son obligatorias porque
se obtienen con `os.environ[...]`; si faltan, Django no puede iniciar. Tienen
valor por defecto `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=""`,
`POSTGRES_HOST="127.0.0.1"` y `POSTGRES_PORT="5432"`. Los valores reales no
se incluyen aquí porque se cargan desde `.env`.

**4. Dependencia de `users.0001_initial`.** La migración depende de
`auth.0012_alter_user_first_name_max_length`. `users.User` hereda de
`AbstractUser`, por lo que su migración inicial crea relaciones con
`auth.Group` y `auth.Permission`. Django necesita que esas tablas y su esquema
actual estén disponibles antes de crear las relaciones `groups` y
`user_permissions` del usuario personalizado.

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

## 2026-08-19 — Módulo Core y página inicial

Se creó la aplicación core para responsabilizarse únicamente de la página inicial y de futuras páginas generales. no contiene modelos, ni reglas del catálogo porque esas responsabilidades perteneceran a apliciones de dominio independientes.

La pagina inicial se desarrolló mediante un flujo test-fists. Primero se definieron pruebas para comprobar que la ruta raiz podía resolverse mediante su nombre, que era pública, que respondia con HTTP 200 y que mostraba el contenido principal esperado. Después se implementaron la URL, la vista y la plantilla mínimas y se ejecutaron nuevamente las pruebas.

La petición GET/ entra por config.urls, se delega en apps.core.urls, ejecuta la vista home y renderiza home.html. LA aplicación no necesita acceder a la base de datos porque la página actual es estática.

## Explicación de la fase

Separé la página principal en una aplicación core para manetener fuera del catálogo las responsabilidades generales del sitio. Definí primero el comportamiento mediante pruebas, implemente la solución mínima y ejecuté después la regresión completa. De esta manera, la estructura modular no es solo organizativa: cada aplicacion de dominio tiene una responsabilidad concreta y verificable.
