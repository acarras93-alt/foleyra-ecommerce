# Requisitos no funcionales

| ID | Requisito | Criterio de verificación | Estado |
| RNF-01 | Los secretos no se almacenarán en el repositorio. | `.env` está ignorado y `.env.example` solo contiene marcadores. | Aprobado |
| RNF-02 | El entorno será reproducible. | Las versiones están bloqueadas y PostgreSQL se ejecuta mediante Docker Compose. | Aprobado |
| RNF-03 | Las reglas de negocio se desarrollarán mediante pruebas. | Cada comportamiento comenzará con una prueba en estado Red. | Aprobado |
| RNF-04 | Los requisitos serán trazables. | Cada requisito se relacionará con pruebas, evidencias y commits. | Aprobado |
| RNF-05 | Web y API compartirán las reglas de negocio. | Ambas interfaces utilizarán los mismos servicios y selectores. | Aprobado |
