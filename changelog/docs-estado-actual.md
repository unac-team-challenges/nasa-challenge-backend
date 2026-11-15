# docs/estado-actual

PR: base `developer`. Solo documentación.

## Cambiado
- `docs/tendencias.md`: ya no es una tarea para Sebastian; describe lo implementado (`pipeline/tendencias.py` escribe, la API sirve `stats` en `/api/zonas`). Se quitó lo «por confirmar» y el reparto de tareas.
- `docs/propuestas-mejora/`: se quitó lo ya aplicado (404 JSON, `Cache-Control`, apagado ordenado, `deny_unknown_fields`, rangos físicos, versiones fijas, `permissions`/`concurrency`/dependabot, Callao, despliegue en Render) y se corrigió el estado del cron (el workflow ya está en `main`, pero nunca se ha ejecutado). El `README` de esa carpeta lista solo lo pendiente.

## Quitado
- `docs/api-stats.md`: la guía de la tarea ya está hecha (#41, `changelog/feat-api-stats.md`).
- `docs/propuestas-mejora/01-api-rust.md`: todo aplicado salvo menores, que pasaron al `README` de la carpeta.

## Notas
- No se tocaron las líneas de `docs/tendencias.md` que cambia #42 (§2b y el semáforo) para no provocar conflictos.
