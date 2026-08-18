---
name: Pytest and PostgreSQL tests
description: Reglas para pruebas pytest y pytest-django ejecutadas con PostgreSQL.
applyTo: "**/tests/**/*.py,**/test_*.py,**/*_tests.py"
---

# Reglas de pruebas

- Usa pytest y pytest-django; no introduzcas otro framework de pruebas.
- Deriva cada prueba de un criterio de aceptación o de una decisión técnica
  verificable.
- Para comportamiento nuevo, ejecuta primero la prueba y confirma que falla por
  la ausencia del comportamiento, no por un error de configuración.
- Usa `@pytest.mark.django_db` únicamente cuando la prueba acceda realmente a la
  base de datos.
- Las pruebas con base de datos deben usar PostgreSQL. No crees ajustes de test
  basados en SQLite.
- Comprueba comportamiento observable y evita acoplar las pruebas a detalles
  internos innecesarios.
- Usa datos mínimos y explícitos; no dependas de datos reales ni de orden entre
  pruebas.
- No debilites, borres o marques una prueba para hacer pasar una implementación.
- Separa preparación, acción y comprobación de forma legible.
- Ejecuta primero el archivo o prueba objetivo y después la batería completa
  con `.venv/bin/python -m pytest -q`.
- Informa del estado Red inicial y del estado Green final con el motivo de cada
  resultado.
