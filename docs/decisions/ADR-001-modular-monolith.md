## ADR-001: monolito modular

- Estado: aceptada

- Contexto: el proyecto debe demostrar Django, backend, comercio digital y API REST dentro de un tiempo limitado

- Decisión: utilizar una sola aplicación desplegable Django, dividida en apps de negocio

- Consecuencias positivas: desarrolloy despliegue sencillos, módulos visibles y transacciones locales

- Consecuencias negativas: los módulos comparten proceso y base de datos. Será necesario controlar sus dependencias.