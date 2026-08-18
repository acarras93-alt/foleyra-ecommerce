---
name: Django and DRF
description: Reglas para implementar y revisar código Django y Django REST Framework.
applyTo: "**/*.py"
---

# Reglas de Django y Django REST Framework

- Mantén las aplicaciones dentro de `apps` y la configuración en `config`.
- Lee los ADR y el requisito aplicable antes de modificar modelos, vistas,
  serializers, servicios o URLs.
- No importes `django.contrib.auth.models.User`.
- Usa `settings.AUTH_USER_MODEL` para `ForeignKey`, `OneToOneField` y
  `ManyToManyField`; usa `get_user_model()` en código ejecutable.
- No añadas campos al usuario personalizado sin un requisito aprobado.
- Configura la base de datos exclusivamente con variables de entorno y el
  backend `django.db.backends.postgresql`.
- No incluyas valores alternativos que activen SQLite.
- Genera migraciones con Django, inspecciónalas y comprueba que no contienen
  cambios ajenos al requisito. No edites una migración generada para silenciar
  herramientas de estilo.
- Mantén las vistas y serializers de DRF delgados. Las reglas compartidas por
  web y API deben residir fuera de las capas de presentación.
- Declara permisos explícitos cuando se implemente una API. No publiques datos
  privados ni rutas internas por defecto.
- Usa transacciones para operaciones de negocio que deban ser atómicas, pero
  solo cuando el requisito lo justifique.
- Evita señales para lógica de negocio central salvo que exista una decisión
  documentada.
- No crees código de catálogo mientras esta fase permanezca cerrada.
