# refactor/zona-recuadro

Punto 2 de lo que dejó Leandro al mezclar el #57 (revisión del #55). Es un refactor: ni los JSON, ni la API, ni OpenAPI cambian.

## Qué cambia
- **`src/models/recuadro.rs` (nuevo):** la macro `zona_recuadro!` define `ZonaVegetacion` y `ZonaCobertura` con sus campos comunes declarados **una sola vez**, y el trait `Comunes` con `comun()`, que entrega esos campos ya listos para validar.
- `vegetacion.rs` y `cobertura.rs` quedan con su struct de año y una llamada a la macro: nombre, tipo del año, nombre del umbral y el texto de los campos cuya explicación cambia.
- `src/data.rs`: el trait `Recuadro` baja de 11 miembros a 4 (`ARCHIVO`, `TENDENCIA_DE`, `revisar`, `anios`) y se va la macro `campos_recuadro!`. `recuadros()` valida con `z.comun()`.
- Un campo común nuevo se añade en un solo sitio (la macro); antes eran tres (`ZonaVegetacion`, `ZonaCobertura` y `campos_recuadro!`).

## Por qué una macro y no un `ZonaRecuadro<A>` genérico
- El umbral se llama distinto en cada JSON (`umbral_verde_ndvi`, `umbral_bosque_pct`): un struct genérico lo tendría que leer con `#[serde(flatten)]`, y con `flatten` serde deja de rechazar campos desconocidos en la zona (los tests `vegetacion_mal_formada_se_rechaza` lo exigen).
- OpenAPI seguiría publicando los nombres `ZonaVegetacion` y `ZonaCobertura` (los usa el front); con un genérico cambiarían.

## Comprobado
- `cargo test`: 35/35 (incluye `openapi_json_esta_al_dia`: `openapi.json` no cambia), `cargo clippy -- -D warnings` y `cargo fmt --check`.
- `bash tests/e2e.sh`: TODO OK.
