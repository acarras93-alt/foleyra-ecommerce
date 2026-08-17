# ADR-002: Uso de PostgreSQL

**Estado:** Aceptada.

## Contexto

El sistema necesita un modelo relacional consistente con el entorno previsto para su ejecución final.

## Decisión

Utilizar PostgreSQL 18.6 desde la primera migración y ejecutarlo localmente mediante Docker Compose.

## Consecuencias

El entorno es reproducible y evita diferencias con SQLite, pero requiere Docker Desktop durante el desarrollo.
