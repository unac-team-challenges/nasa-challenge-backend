# docs/propuestas-mejora

## Añadido
- `docs/propuestas-mejora/`: revisión del backend (rama `developer` @ `7fc8c70` y PR #21) con fallas encontradas y mejoras propuestas. Cada punto explica por qué importa y cómo se arreglaría.
  - `README.md`: resumen y tabla de prioridades.
  - `01-api-rust.md`: API Axum (404 JSON, `Cache-Control`, apagado ordenado, `deny_unknown_fields`, notas del PR #21).
  - `02-pipeline-y-datos.md`: IMERG V07 termina en 2025-09 y empieza en 1998-01 (verificado en CMR), Callao sin celdas POWER, reintentos, dependencias sin versión.
  - `03-ci-cd-y-repo.md`: el cron nunca corre (workflow fuera de `main`), commit del bot sin `e2e`, despliegue en Vercel, PR #18 huérfano.
  - `04-flujos-y-tecnologias.md`: proyectos parecidos, flujo "static-first" con espejo generado desde la API, tecnologías que encajan y cuáles no.

## Corregido
- Nada. Este PR no cambia código ni datos.

## Pendiente
- Que el equipo decida qué propuestas se adoptan. Cada una iría en su propio PR.
