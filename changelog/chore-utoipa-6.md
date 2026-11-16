# chore/utoipa-6

`utoipa` 5 → 6 (pendiente de `docs/propuestas-mejora/README.md`).

## Cambiado
- `Cargo.toml` y `Cargo.lock`: `utoipa = "6"` (6.0.0; `utoipa-gen` 6.0.1). Compila sin cambios de código.
- `openapi.json` regenerado (`UPDATE_OPENAPI=1 cargo test openapi`). Único cambio: utoipa 6 ya no escribe `"description": ""`
  en las 10 respuestas que no tenían texto. Rutas, parámetros y esquemas son los mismos.

## Contrato con el frontend
Se generaron los tipos con `openapi-typescript` 7.13.0 (el del frontend) desde el `openapi.json` viejo y desde el nuevo:
`schema.d.ts` sale **idéntico**. El frontend no necesita cambios.

## Nota
En OpenAPI 3.1 `description` es obligatorio en cada respuesta; utoipa 6 lo omite cuando está vacío. Si algún validador estricto
se queja, la solución es poner un texto en cada `responses(...)` de `src/routes/`, en un PR aparte.

`docs/propuestas-mejora/README.md` ya no lista «`utoipa` 6» entre los pendientes (se quitó al mezclar con `developer`, tras #80).
