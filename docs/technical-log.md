## 2026-08-17 — Corrección y fijación del entorno Python

### Contexto

El entorno virtual inicial se había creado con Python 3.14.0,
mientras que la versión aprobada para el proyecto era Python 3.12.

### Decisión

Se seleccionó Python 3.12.13 y se fijó mediante `pyenv` y el fichero
`.python-version`.

### Acciones realizadas

1. Se actualizó `pyenv`.
2. Se instaló Python 3.12.13.
3. Se fijó la versión local del proyecto.
4. Se recreó `.venv` con el intérprete correcto.
5. Se generaron los bloqueos de dependencias con `pip-compile`.
6. Se sincronizó el entorno mediante `pip-sync`.
7. Se verificaron las versiones y la integridad de las dependencias.

### Resultado

- Python 3.12.13
- Django 5.2.17
- Django REST Framework 3.18.0
- Psycopg 3.3.4
- pytest 9.1.1
- Ruff 0.16.3
- `pip check`: sin dependencias incompatibles

### Evidencias

Las capturas de instalación y verificación se incorporaron al manual
de instalación

## 2026-08-18 — Cierre del checkpoint de infraestructura

### Completado

- Entorno virtual con Python 3.12.13.
- Dependencias bloqueadas y verificadas.
- Variables de entorno separadas del código.
- PostgreSQL 18.6 ejecutado mediante Docker Compose.
- Conexión con PostgreSQL verificada.
- Decisiones de infraestructura documentadas.
- Commits de infraestructura y documentación realizados.

### Siguiente fase

Crear la estructura Django, configurar PostgreSQL, definir el usuario personalizado y ejecutar la primera migración.
