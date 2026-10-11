---
name: write-tests
description: Escribe la prueba mínima para un criterio aprobado y comprueba su estado real.
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
3. resume el comportamiento observable en una o dos frases e indica qué
   prueba existente reutilizar o ampliar y cuándo hace falta una nueva;
4. comprueba que no hay cambios previos que debas preservar.

Aplica la [premisa de cierre acordada el 2026-10-07](../../docs/requirements/mvp-implementation-plan.md#4-premisa-de-trabajo-hasta-el-cierre-del-proyecto).
Puedes redactar la prueba completa. Explica al desarrollador qué prepara, qué
operación ejecuta y qué fallo detectan sus comprobaciones. No exijas un análisis
exhaustivo de la infraestructura; profundiza cuando exista una ambigüedad que
cambie el comportamiento, un riesgo concreto o una parte del criterio sin cubrir.

Después:

- añade el caso mínimo y legible;
- no modifiques código de producción, migraciones ni dependencias;
- ejecuta solo la prueba objetivo;
- si falta comportamiento, confirma que falla por ese motivo;
- si pasa por comportamiento existente, comprueba que demuestra el criterio y
  registra el Green inicial sin forzar un fallo ni cambiar producción;
- si falla por configuración o por una expectativa incorrecta, corrige la
  prueba y vuelve a ejecutarla;
- informa de los archivos modificados, el comando, el resultado y su causa.

No hagas commits y no continúes con la implementación en este mismo paso.
