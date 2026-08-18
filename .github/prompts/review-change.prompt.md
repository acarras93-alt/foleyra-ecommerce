---
name: review-change
description: Revisa cambios pendientes sin editar y prioriza defectos verificables.
agent: ask
argument-hint: "scope=working-tree"
---

Revisa `${input:scope:working-tree}` sin modificar archivos.

Consulta las [instrucciones del repositorio](../copilot-instructions.md), el
requisito implicado, los ADR y el diff completo.

Comprueba:

1. correspondencia con el requisito y sus criterios de aceptación;
2. defectos funcionales y casos límite;
3. autenticación, autorización, exposición de datos y secretos;
4. uso exclusivo de PostgreSQL;
5. uso correcto de `AUTH_USER_MODEL`;
6. necesidad, orden y contenido de migraciones;
7. calidad y suficiencia de las pruebas;
8. cambios ajenos al alcance y dependencias no autorizadas;
9. documentación y trazabilidad;
10. comandos de verificación que todavía falten.

Presenta primero los hallazgos ordenados por severidad, con archivo y línea.
Después incluye preguntas abiertas y un resumen breve. Si no encuentras
defectos, dilo expresamente y enumera los riesgos o verificaciones que no hayas
podido cubrir.

No edites, no ejecutes migraciones destructivas y no hagas commits.
