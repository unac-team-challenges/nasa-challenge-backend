# fix/openapi-description

Cierra la deuda anotada en `changelog/chore-utoipa-6.md`: utoipa 6 deja de escribir `"description": ""`, y en OpenAPI 3.1 `description` es obligatorio en cada respuesta.

## Cambiado
- `src/routes/api.rs`: las 10 respuestas de `/api/*` llevan `description` (200: qué devuelve; 400: «Falta `variable` o no es válida»; 404: «La zona no existe»).
- `openapi.json` regenerado (`UPDATE_OPENAPI=1 cargo test openapi`): ya no hay ninguna respuesta sin `description`.
- `Cargo.lock`: `cargo` volvió a escribir `syn 2.0.119` y las referencias `syn 3.0.10`, que se habían perdido al mezclar #81 con #82.

## Contrato con el frontend
Con `openapi-typescript` 7.13.0, `schema.d.ts` solo gana comentarios `@description` en las 10 respuestas; ningún tipo cambia. El frontend puede copiar el `openapi.json` nuevo cuando quiera (`pnpm gen`), no es urgente.

## Notas
- El log de peticiones ya incluye la query (`uri=/api/zonas?variable=lluvia`), comprobado en vivo con `cargo run`.

## Pendiente
- Nada.
