---
name: plan-requirement
description: Planifica un requisito aprobado sin modificar archivos.
agent: plan
argument-hint: "requirementId=RF-XX"
---

Planifica el requisito `${input:requirementId:RF-XX}` sin editar archivos.

Lee las [instrucciones del repositorio](../copilot-instructions.md), los
[requisitos funcionales](../../docs/requirements/functional-requirements.md),
los [requisitos no funcionales](../../docs/requirements/non-functional-requirements.md)
y los [ADR](../../docs/decisions/).

Si el requisito no está aprobado o sus criterios de aceptación son
insuficientes, enumera los huecos y detente.

Entrega exactamente:

1. objetivo y criterios cubiertos;
2. alcance y elementos fuera de alcance;
3. archivos que sería necesario leer y posiblemente modificar;
4. diseño mínimo y decisiones que requieren aprobación;
5. impacto en PostgreSQL y necesidad o no de migración;
6. plan de pruebas con estado Red esperado;
7. comandos de verificación;
8. riesgos de seguridad, permisos y privacidad;
9. secuencia de commits pequeños, todos en estado válido.

No escribas código, no cambies dependencias, no ejecutes migraciones y no hagas
commits.
