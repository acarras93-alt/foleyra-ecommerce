---
name: write-tests
description: Escribe la prueba mínima para un criterio aprobado y confirma el estado Red.
agent: agent
argument-hint: "requirementId=RF-XX criterion=CA-RFXX-XX"
---

Escribe únicamente las pruebas del criterio
`${input:criterion:CA-RFXX-XX}` perteneciente al requisito
`${input:requirementId:RF-XX}`.

Aplica las [instrucciones de pruebas](../instructions/testing.instructions.md)
y consulta el requisito en
[requisitos funcionales](../../docs/requirements/functional-requirements.md).

Antes de editar:

1. confirma que el requisito y el criterio están aprobados;
2. localiza las pruebas y la implementación relacionadas;
3. explica qué comportamiento observable comprobará la prueba;
4. comprueba que no hay cambios previos que debas preservar.

Después:

- añade el caso mínimo y legible;
- no modifiques código de producción, migraciones ni dependencias;
- ejecuta solo la prueba objetivo;
- confirma que falla por la ausencia del comportamiento esperado;
- si falla por configuración o por una expectativa incorrecta, corrige la
  prueba y vuelve a ejecutarla;
- informa de los archivos modificados, el comando y el motivo exacto del fallo.

No hagas commits y no continúes con la implementación en este mismo paso.
