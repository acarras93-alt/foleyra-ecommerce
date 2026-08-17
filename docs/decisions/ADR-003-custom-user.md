# ADR-003: Usuario personalizado

**Estado:** Aceptada.

## Contexto

Modificar el modelo de usuario después de generar las primeras migraciones puede requerir cambios complejos en las relaciones y la base de datos.

## Decisión

Crear un modelo de usuario personalizado antes de ejecutar la primera migración.

## Consecuencias

El sistema queda preparado para futuras ampliaciones sin modificar posteriormente la identidad principal de los usuarios.
