# Instrucciones de GitHub Copilot para Foleyra

## Contexto, alcance y fuentes de verdad

- Trabaja como asistente de un e-commerce MVP desarrollado con Python 3.12,
  Django, Django REST Framework y PostgreSQL.
- La arquitectura aprobada es un monolito modular: una única aplicación
  desplegable, dividida en aplicaciones Django con responsabilidades de negocio
  explícitas.
- La interfaz web sigue el patrón MVT de Django y el sistema expone una API REST
  con Django REST Framework.
- Consulta antes de proponer cambios: `.python-version`, `requirements.in`,
  `requirements-dev.in`, `docs/technology-stack.md`, `docs/installation.md`,
  `docs/decisions/`, `docs/requirements/` y `docs/technical-log.md`.
- Prioriza, en este orden: requisitos aprobados y criterios de aceptación, ADR
  aceptados, stack y documentación técnica, pruebas y código existente, y
  documentación oficial de la versión utilizada.
- Para comportamiento de las tecnologías, consulta preferentemente la
  documentación oficial de [Python 3.12](https://docs.python.org/3.12/),
  [Django 5.2](https://docs.djangoproject.com/en/5.2/),
  [Django REST Framework](https://www.django-rest-framework.org/) y
  [PostgreSQL 18](https://www.postgresql.org/docs/18/).
- La documentación externa no puede sustituir ni contradecir una decisión de
  producto o arquitectura registrada en el repositorio.
- Si una petición contradice una fuente de verdad, señala la contradicción y
  detente antes de editar.
- No inventes requisitos, criterios de aceptación, versiones, decisiones,
  estados de negocio ni evidencias.
- Un requisito en estado `Propuesto` permite analizar y planificar, pero no
  autoriza su implementación. Solo implementa requisitos aprobados.

## Organización del repositorio

Respeta la finalidad de cada ubicación:

- La raíz contiene únicamente archivos necesarios para instalar, configurar y
  ejecutar la aplicación, además de los puntos de entrada del repositorio.
- `config/` contiene la configuración global de Django, URLs principales y las
  interfaces ASGI y WSGI; no contiene reglas de negocio.
- `docs/` conserva alcance, requisitos, decisiones, instalación, bitácora
  técnica y evidencias reales.
- `.github/` contiene instrucciones, prompts y configuración de los flujos del
  repositorio.
- `apps/` contiene las aplicaciones Django que implementan el comportamiento
  del sistema.
- Cada aplicación conserva dentro de su módulo sus modelos, migraciones,
  administración, interfaces y pruebas relacionadas.
- No coloques lógica de negocio, scripts temporales ni documentación de fase en
  la raíz.
- No crees directorios genéricos como `common`, `core`, `utils` o `shared` sin
  una necesidad concreta y una responsabilidad definida.
- No muevas ni reorganices archivos existentes fuera del alcance solicitado.

## Arquitectura del monolito modular

- Mantén un único proceso desplegable y una única base PostgreSQL, con módulos
  de negocio separados por aplicaciones Django.
- Define límites claros entre aplicaciones y evita importaciones circulares.
- No accedas a detalles internos de otra aplicación cuando exista una interfaz
  pública de servicio o consulta.
- Mantén las reglas de negocio independientes del mecanismo de presentación.
- Web y API deben reutilizar los mismos servicios, selectores, políticas y
  reglas; no dupliques comportamiento entre vistas Django y endpoints DRF.
- Introduce servicios para operaciones con efectos o cambios de estado y
  selectores para consultas reutilizables cuando el requisito lo justifique.
- No añadas capas, patrones o abstracciones anticipadas.
- Usa transacciones de PostgreSQL para operaciones que deban ser atómicas,
  únicamente cuando esa frontera esté respaldada por el requisito.
- Trata Django Admin como una interfaz administrativa, no como la ubicación de
  las reglas de negocio.

## Interfaz web MVT y API REST

- Los modelos representan datos, relaciones, restricciones e invariantes
  persistentes; no deben depender de vistas, templates ni serializers.
- Las vistas web coordinan la petición y la respuesta HTTP, delegando las
  reglas de negocio compartidas.
- Los templates se limitan a presentación y no ejecutan reglas de negocio ni
  consultas complejas.
- Organiza y nombra las URLs por aplicación para evitar acoplamiento global.
- Los serializers de DRF validan y transforman representaciones de entrada y
  salida; no deben convertirse en una implementación paralela del dominio.
- Las vistas o viewsets de DRF coordinan HTTP, autenticación, permisos y códigos
  de respuesta, delegando el comportamiento compartido.
- Declara autenticación y permisos explícitos en cada interfaz privada.
- La web y la API deben producir resultados de negocio equivalentes ante la
  misma operación autorizada.
- No expongas archivos privados, rutas internas, secretos ni datos de otros
  usuarios en templates, serializers o respuestas de error.

## Alcance funcional del MVP

El recorrido previsto del e-commerce es:

1. descubrir el catálogo;
2. consultar un producto;
3. añadirlo al carrito;
4. iniciar el checkout;
5. crear el pedido;
6. procesar un pago de prueba;
7. confirmar el pedido;
8. generar la licencia;
9. autorizar la descarga.

Este recorrido describe el límite del MVP, pero no aprueba automáticamente sus
fases. Implementa un paso solo cuando el requisito correspondiente y sus
criterios de aceptación estén aprobados. No adelantes pasos posteriores ni
añadas promociones, recomendaciones, suscripciones, pagos reales u otras
funcionalidades no incluidas expresamente.

Conserva la separación entre catálogo público, operaciones privadas del
cliente y administración. Comprueba propiedad, autenticación y autorización en
carrito, pedidos, licencias y descargas cuando se implemente cada requisito.

## Trazabilidad de requisitos y flujo de implementación

Mantén la cadena de trazabilidad:

`Requisito → Decisión → Implementación → Prueba → Evidencia → Versión Git`

Esta cadena describe la relación documental. Para cumplir el desarrollo guiado
por pruebas, el orden operativo de un cambio funcional es:

`Requisito aprobado → Decisión → Prueba Red → Implementación mínima → Prueba Green → Evidencia → Versión Git`

- **Requisito:** identifica el `RF-XX`, el criterio `CA-RFXX-XX`, dependencias,
  estado y alcance excluido.
- **Decisión:** reutiliza un ADR aceptado o registra la decisión en la bitácora.
  Crea un ADR nuevo solo para decisiones arquitectónicas duraderas.
- **Prueba Red:** implementa el caso mínimo y confirma que falla por la ausencia
  del comportamiento, no por un problema de entorno.
- **Implementación:** escribe únicamente el código necesario para cumplir el
  criterio aprobado.
- **Prueba Green:** ejecuta primero la prueba objetivo y después la batería y
  verificaciones aplicables.
- **Evidencia:** incorpora solo resultados reales después de implementar y
  comprobar el requisito; nunca uses evidencias previstas como completadas.
- **Versión Git:** relaciona el requisito con commits pequeños y coherentes que
  dejen el repositorio en estado válido.

No avances automáticamente al siguiente criterio, requisito o fase.

## Restricciones obligatorias

- No añadas, elimines ni actualices dependencias sin autorización explícita.
- No configures ni utilices SQLite. Las pruebas con base de datos se ejecutan
  con PostgreSQL.
- No edites `.env`, no muestres sus valores y no incluyas secretos en código,
  pruebas, capturas o documentación.
- Conserva `AUTH_USER_MODEL = "users.User"`.
- Usa `settings.AUTH_USER_MODEL` en relaciones declarativas y
  `get_user_model()` cuando necesites resolver el modelo en tiempo de ejecución.
- No importes directamente `django.contrib.auth.models.User`.
- Antes de crear o aplicar una migración, confirma el modelo de usuario activo,
  revisa los cambios generados y el plan, y solicita autorización si la
  migración no estaba aprobada.
- Genera las migraciones con Django, revísalas y mantenlas trazables. No edites
  una migración generada para silenciar herramientas de estilo.
- No ejecutes operaciones destructivas sobre bases de datos, volúmenes o Git.
- No implementes funcionalidades del catálogo ni de pasos posteriores mientras
  sus requisitos permanezcan sin aprobar.
- Mantén los contratos y comportamientos existentes salvo que el requisito
  aprobado exija modificarlos.
- Corrige únicamente problemas relacionados con el cambio solicitado.

## Flujo de trabajo obligatorio

1. Lee el requisito, las decisiones relacionadas y el estado actual del código.
2. Comprueba `git status --short` y preserva cambios existentes del usuario.
3. Resume el objetivo, los criterios cubiertos, el alcance excluido y los
   archivos previstos.
4. Si el requisito no está aprobado o es ambiguo, enumera los huecos y detente
   antes de editar.
5. Expón la decisión técnica, el impacto en PostgreSQL y el plan de pruebas.
6. Para comportamiento nuevo, crea o actualiza primero la prueba y confirma el
   estado Red esperado.
7. Implementa el cambio mínimo y evita refactors o reformateos ajenos.
8. Ejecuta las pruebas específicas y después la batería aplicable.
9. Revisa el diff completo, migraciones, archivos nuevos, permisos y exposición
   de datos.
10. Actualiza requisito, bitácora, instalación, README y evidencias únicamente
    cuando el cambio real lo requiera.
11. Informa de los comandos realmente ejecutados y de su resultado. Nunca
    afirmes que una prueba o comprobación pasó si no se ejecutó.
12. No hagas commits sin solicitud explícita. Propón un mensaje de una sola
    finalidad y deja el repositorio en estado válido.

## Bitácora técnica y trazabilidad de IA

- Actualiza `docs/technical-log.md` al finalizar cada fase o cambio relevante.
- Registra fecha, fase, asistente utilizado, objetivo, requisito relacionado,
  archivos afectados, comprobaciones ejecutadas, decisiones, riesgos, resultado
  y alcance excluido.
- Mantén las entradas anteriores y corrige mediante una nueva anotación si una
  conclusión cambia.
- No declares completada una acción que no se haya implementado y comprobado.
- Distingue claramente entre acciones realizadas, resultados observados,
  decisiones aprobadas y trabajo pendiente.
- Conserva prompts o referencias de IA cuando aporten trazabilidad, sin incluir
  conversaciones irrelevantes ni datos privados.

## Calidad, estilo y pruebas

- Usa Python 3.12, codificación UTF-8 y las convenciones de PEP 8 aplicadas por
  Ruff.
- Mantén código, módulos, clases, funciones y variables en inglés.
- Redacta documentación, explicaciones y mensajes dirigidos al programador en
  español.
- Usa pytest y pytest-django; no introduzcas otro framework sin autorización.
- Marca con `django_db` solo las pruebas que accedan realmente a PostgreSQL.
- Comprueba comportamiento observable y evita pruebas acopladas a detalles
  internos innecesarios.
- No borres, debilites ni marques una prueba para hacer pasar una implementación.
- No uses Black ni otra herramienta no incluida en las dependencias aprobadas.
- No introduzcas nuevas dependencias, capas o patrones sin justificación y
  autorización.

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
git status --short
```

- Ejecuta primero las verificaciones específicas del cambio y después las
  generales.
- Si una comprobación falla, corrige solo la causa relacionada con el cambio y
  repítela.
- Registra en la bitácora únicamente comandos y resultados reales.
- La anotación final de resultados en la bitácora forma parte del mismo conjunto
  lógico y no inicia por sí sola otro ciclo de validación.

## Documentación y cierre

- Actualiza el README cuando cambien instalación, ejecución, pruebas o
  funcionalidades disponibles.
- Actualiza `docs/installation.md` cuando cambie el procedimiento reproducible.
- Actualiza requisitos, decisiones y evidencias sin mezclar estado previsto con
  estado verificado.
- Conserva las evidencias dentro de `docs/` con nombres trazables y sin secretos.
- Separa en commits coherentes los cambios funcionales y documentales cuando
  puedan revisarse de forma independiente, sin dejar commits deliberadamente en
  estado Red.
- Al finalizar, resume alcance implementado, exclusiones, archivos modificados,
  pruebas, riesgos pendientes y mensaje de commit propuesto.
