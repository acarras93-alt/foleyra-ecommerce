# Manual de instalación

Este documento describe cómo preparar y ejecutar el proyecto desde un entorno limpio.

## 1. Prerrequisitos

- Git.
- Python 3.12.13.
- Docker Desktop con Docker Compose.

pyenv y Visual Studio Code son herramientas opcionales. La instalación descrita
es para desarrollo local con PostgreSQL, no un despliegue en producción.

## 2. Creación del entorno virtual

Desde un directorio de trabajo, si todavía no tienes el repositorio:

```bash
git clone https://github.com/acarras93-alt/foleyra-ecommerce.git
cd foleyra-ecommerce
```

Desde la raíz del repositorio, con Python 3.12.13 disponible:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

Si ya existe `.venv`, actívalo y comprueba su versión antes de continuar.

## 3. Instalación de dependencias bloqueadas

```bash
python -m pip install --require-hashes -r requirements-dev.txt
python -m pip check
```

Se utilizan los ficheros bloqueados existentes. No es necesario regenerarlos
ni actualizar dependencias para instalar esta versión.

## 4. Configuración de variables de entorno

Crea `.env` a partir de `.env.example` únicamente si no existe:

```bash
test -e .env || cp .env.example .env
```

Edita el archivo local para proporcionar tus valores de `DJANGO_SECRET_KEY` y
las variables PostgreSQL. Django y Docker Compose deben usar las mismas
credenciales. Para la configuración local, PostgreSQL se expone en
`127.0.0.1:5432`, salvo que hayas cambiado el puerto. `.env` está ignorado:
no lo añadas a Git ni incluyas sus valores en capturas o documentación.

## 5. Arranque de PostgreSQL

Abre Docker Desktop y espera a que su motor esté disponible. Después:

```bash
docker compose up -d db
docker compose ps
```

Espera a que `db` figure como `healthy`. Se utiliza la imagen
`postgres:18.6-alpine` y el volumen `postgres_data`; no borres el volumen para
actualizar el código o ejecutar pruebas.

## 6. Verificaciones

```bash
python --version
python -m pip check
docker compose ps
```

Las comprobaciones de Django y migraciones del apartado siguiente requieren
que PostgreSQL esté accesible. Si falla la conexión, comprueba el motor Docker,
el estado de `db`, el puerto y la coherencia de la configuración local.

## 7. Django

### 7.1. Estructura inicial

El proyecto utiliza `config` para la configuración global y agrupa las
aplicaciones de negocio bajo `apps`. La primera aplicación es `apps.users`,
que define el modelo de usuario personalizado `users.User`.

La variable `AUTH_USER_MODEL` se configuró antes de generar o aplicar ninguna
migración. La conexión `default` utiliza exclusivamente el backend de
PostgreSQL y obtiene sus credenciales desde `.env`.

### 7.2. Aplicación de las migraciones versionadas

Con el contenedor de PostgreSQL en estado saludable:

```bash
python manage.py migrate --plan
python manage.py migrate
python manage.py showmigrations catalog orders
```

Para instalar el proyecto se aplican las migraciones existentes; no se generan
otras nuevas. El modelo activo es `users.User`; se crea `users_user`, no
`auth_user` del modelo sustituido.

La migración `catalog.0001_initial` se generó con Django, se revisó mediante
`migrate catalog --plan` y se aplicó después sobre PostgreSQL. Crea las tablas
de categorías, productos, tipos de licencia y ofertas producto-licencia; no
incorpora modelos de suscripción, pedido, pago ni descarga. Es una descripción
histórica de esa migración, no del esquema completo actual.

La versión actual incorpora además pedidos, intentos de pago y permisos:
`catalog.0003` añade las condiciones e identidades declaradas;
`orders.0006` crea `LicenseGrant`; `orders.0007` amplía los datos históricos;
`orders.0008` añade `source_product` y `orders.0009` añade
`source_license_type`, ambos protegidos contra borrado. Las relaciones admiten
nulo para compras antiguas y no realizan un mapeo automático. Las compras
antiguas se regularizan mediante operaciones explícitas, descritas en
[las evidencias de RF-10](evidence/RF-10/README.md).

Tras preparar la base de datos:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El admin actual registra usuarios; la gestión
del catálogo y de pedidos sigue pendiente de RF-15. No se incluye todavía
una carga automática del catálogo de demostración. Las pruebas construyen
sus propios datos en una base PostgreSQL de pruebas separada.

### 7.3. Verificaciones

```bash
python manage.py check --database default
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
python -m pip check
```

Estas comprobaciones validan la configuración de Django, la ausencia de
cambios de modelo sin migración, el uso del usuario personalizado, su
persistencia en PostgreSQL y la calidad estática del código.

La ejecución de pytest requiere una cuenta PostgreSQL con permiso para crear
su base de pruebas. Un error de conexión o permisos no acredita un fallo de
una regla de negocio; corrige el entorno y repite la comprobación.

### 7.4. Evidencias del checkpoint

El inventario de capturas, sus comandos reproducibles y las reglas para no
exponer secretos se encuentran en
[`docs/evidence/phase-01/README.md`](evidence/phase-01/README.md).

El prompt empleado durante esta inicialización y el alcance real de la
asistencia de IA se registran en
[`docs/ai-assisted-development.md`](ai-assisted-development.md).

La revisión del 2026-10-14 y sus límites figuran en
[las evidencias de RF-10](evidence/RF-10/README.md). Los pasos anteriores
documentan la configuración reproducible; esta revisión no certifica una
instalación en una máquina limpia ni una demo con productos sonoros reales.
