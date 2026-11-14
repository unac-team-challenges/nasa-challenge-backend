# refactor/arquitectura-api

## Cambiado
- `src/main.rs` (todo junto) dividido en módulos: `lib.rs`, `config.rs`, `data.rs`, `error.rs`, `schema.rs`, `models/`, `routes/`.
- `power.json` se lee a structs tipados (`models/power.rs`) en vez de `serde_json::Value`: un campo faltante, mal escrito o `null` impide arrancar.
- Búsqueda por índice `HashMap`; ignora mayúsculas y tildes (`/power/ancash` = `/power/Áncash`).
- Errores como JSON: `{"error": "región 'x' no encontrada"}` (sigue siendo 404).
- CORS: orígenes extra por la variable `CORS_ORIGINS` (sin recompilar), además de localhost.

## Añadido
- `GET /health`.
- `tests/api.rs`: 7 tests de integración con `cargo test` (sin abrir puerto).
- `tests/e2e.sh` ahora también corre `cargo test` y prueba `/health` y búsqueda sin tilde.

## Notas
- Las respuestas de `/regiones` y `/power/{region}` mantienen la misma forma que antes.
