# feat/openapi-utoipa

Base: `developer`. Incluye las rutas `/api/*` de #18, que se mezcló en `feat/api-gpm` (ya mezclada) y nunca llegó a `developer`.

## Añadido
- `utoipa` 5: `ToSchema` en los structs de `schema.rs` y en `Variable`; `#[utoipa::path]` en las 3 rutas `/api/*`.
- `src/openapi.rs` (`ApiDoc`) y `GET /api/openapi.json`.
- `openapi.json` en la raíz: el contrato que copia el frontend (`src/api/openapi.json` → `pnpm gen`).
- Tests: `openapi_json_esta_al_dia` (falla si el archivo quedó viejo; se regenera con `UPDATE_OPENAPI=1 cargo test openapi`) y `openapi_se_sirve_con_las_3_rutas`.

## Pendiente
- `stats` de cada zona, `/api/casos/{id}` y `/api/hallazgos` cuando existan las tendencias.
