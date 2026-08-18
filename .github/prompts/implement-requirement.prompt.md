---
name: implement-requirement
description: Implementa el cambio mínimo que hace pasar una prueba aprobada.
agent: agent
argument-hint: "requirementId=RF-XX criterion=CA-RFXX-XX"
---

Implementa el cambio mínimo para el criterio
`${input:criterion:CA-RFXX-XX}` del requisito
`${input:requirementId:RF-XX}`.

Lee las [instrucciones del repositorio](../copilot-instructions.md), las
[reglas de Django](../instructions/django.instructions.md) y el requisito
correspondiente en
[requisitos funcionales](../../docs/requirements/functional-requirements.md).

Condiciones previas:

1. debe existir una prueba aprobada que falle por el motivo esperado;
2. el requisito y el criterio deben estar aprobados;
3. el plan debe identificar si existen cambios de modelo o migraciones.

Durante la implementación:

- no cambies la prueba para acomodar una implementación incorrecta;
- no añadas dependencias;
- no amplíes el alcance ni hagas refactors no solicitados;
- si aparece una migración no prevista, detente y solicita aprobación;
- preserva los cambios existentes del usuario.

Al terminar:

1. ejecuta la prueba objetivo hasta obtener Green;
2. ejecuta la batería completa y las verificaciones base aplicables;
3. revisa el diff y señala cualquier riesgo pendiente;
4. informa de los comandos ejecutados y sus resultados reales;
5. propone un mensaje de commit de una sola finalidad.

No hagas commits sin autorización explícita.
