# Manual de instalación y recorrido manual

Este documento describe cómo preparar Foleyra desde un entorno limpio y cómo
validar manualmente el recorrido de compra y descarga del maestro. La instalación
es local para desarrollo; no configura un despliegue de producción.

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
ni actualizar dependencias para instalar esta versión. Los bloqueos incorporan
`soundfile==0.13.1` y sus dependencias para inspeccionar FLAC/AIFF. Tras instalar,
puedes comprobar el lector de audio con:

```bash
python -c "import soundfile; print(soundfile.__version__, soundfile.__libsndfile_version__)"
```

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

`catalog.0004` crea `MasterAudioPreparation` y `catalog.0005` conserva su fecha
de creación. `orders.0010` añade `OrderItem.master_preparation` con `PROTECT` y
nulo para líneas antiguas de desarrollo, sin asignarles un archivo por
inferencia. Cada nueva compra captura el maestro preparado en su línea.

Las previews y los maestros se guardan en `media/` y `private_media/`. El
maestro no tiene URL pública. La ruta `/licenses/<id>/download/` comprueba la
sesión, la propiedad de la licencia, el estado pagado del pedido y la
preparación capturada antes de transmitir los bytes como adjunto. Deben
respaldarse PostgreSQL y `private_media/` conjuntamente: la base de datos
conserva la referencia y el almacenamiento conserva el archivo.

Tras preparar la base de datos:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. En `/admin/`, un superusuario puede gestionar
categorías, productos, tipos de licencia y ofertas; los pedidos, líneas,
intentos de pago y licencias se consultan en modo de solo lectura. El proyecto
no carga datos de demostración automáticamente.

### 7.3. Preparar un producto de demostración

Para recorrer la compra y descarga se necesita una categoría, un producto, un
tipo de licencia, una oferta activa y un archivo maestro WAV/BWF, FLAC o AIFF
válido de al menos 48 kHz y 24 bits. Crea los datos de catálogo desde Django
Admin y anota el identificador del producto. El formulario de producto no sube
maestros; para esta versión la asociación se realiza mediante el servicio de
dominio. Usa un archivo cuyo uso y entrega estén autorizados; no es necesario
copiar la biblioteca completa al repositorio.

En otra terminal, activa el mismo entorno virtual y abre el shell de Django:

```bash
python manage.py shell
```

Adapta la ruta, el identificador y los metadatos reales del archivo:

```python
from pathlib import Path
from django.core.files import File
from apps.catalog.services import set_product_master_audio

master_path = Path("/ruta/local/al/maestro.wav")
product_id = 1

with master_path.open("rb") as source:
    preparation = set_product_master_audio(
        product_id=product_id,
        uploaded_file=File(source, name=master_path.name),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

print(preparation.storage_key, preparation.audio_format)
```

El servicio valida el contenido real y guarda el archivo en almacenamiento
privado con una clave nueva. Si el archivo no coincide con el formato o las
propiedades declaradas, la operación falla. Repite la ruta y los metadatos
según corresponda para FLAC o AIFF. El comprador de prueba debe ser una cuenta
normal registrada desde la web, no el superusuario.

### 7.4. Verificaciones

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

La puerta de calidad registrada el 2026-10-26 obtuvo **434 pruebas aprobadas**
y superó `manage.py check`, las comprobaciones de migraciones, Ruff y `pip check`;
el detalle está en
[`docs/evidence/RF-15/quality-gate-2026-10-26.md`](evidence/RF-15/quality-gate-2026-10-26.md).
La ejecución de pytest requiere una cuenta PostgreSQL con permiso para crear
su base de pruebas. Un error de conexión o permisos indica un problema del
entorno; corrígelo y vuelve a ejecutar las comprobaciones.

### 7.5. Recorrido manual de compra y descarga

Esta comprobación se realiza desde el navegador con PostgreSQL activo, las
migraciones aplicadas, una cuenta de cliente y un producto con oferta y maestro
preparado. Las pruebas automatizadas usan archivos temporales; esta comprobación
manual confirma además la interacción visual y el archivo que recibe el
navegador. El pago es simulado y no se realiza ningún cobro real.

1. Abre `http://127.0.0.1:8000/` e inicia sesión como cliente.
2. Busca el producto, abre su detalle y escucha la preview si está disponible.
3. Añade una oferta al carrito, revisa el contenido y crea el pedido.
4. Desde «Mis pedidos», aprueba el pago simulado. Comprueba que el pedido queda
   pagado y que aparece el derecho adquirido.
5. Abre «Mis licencias», consulta las condiciones y solicita la descarga.
6. Comprueba que el navegador recibe el archivo esperado, con el nombre y la
   extensión correspondientes, y que puedes abrirlo o reproducirlo.

El resultado esperado es que el pago conceda el derecho, pero no inicie la
descarga automáticamente. La descarga comienza cuando el cliente pulsa el
enlace de su licencia y corresponde al maestro capturado para esa línea en el
checkout, aunque el catálogo cambie después. Cada línea tiene su descarga
individual; no se genera un ZIP. Las capturas del recorrido manual se incluyen
en las evidencias de entrega. Para la matriz de criterios y detalles de RF-11,
consulta [los requisitos funcionales](requirements/functional-requirements.md).
