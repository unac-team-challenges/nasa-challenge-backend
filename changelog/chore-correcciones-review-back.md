# chore/correcciones-review-back

Las 7 mejoras de la review de `main...developer` (#45–#48). Sin cambios de contrato:
`openapi.json`, rutas y forma de las respuestas siguen igual.

## CI y workflows
- `ci.yml`: nuevo paso que regenera `pipeline/requirements.lock` con `uv` y falla si difiere
  de lo commiteado. dependabot solo actualiza `requirements.txt`; antes el CI salía verde
  probando las versiones viejas del lock.
- `actualizar-datos.yml`: `gh pr create` ya no se traga los errores con `|| echo`; si falla,
  el job queda en rojo con el error real.
- `actualizar-datos.yml`: fuera `git push --force`. Si la rama del día ya existe (segunda
  ejecución el mismo día), el job falla con un mensaje claro en vez de pisarla.
- `rust-toolchain.toml`: Rust fijado en `1.99.0` (con `rustfmt` y `clippy`). Una estable
  nueva con lints nuevos ya no pone el CI en rojo sin tocar código.

## Rendimiento de la API
- `GET /api/openapi.json`: el documento se genera una sola vez (`LazyLock`) y se sirve como
  `&'static str`, en vez de reconstruir y serializar utoipa en cada petición.
- `/power/{region}` y `/gpm/{region}`: se serializa la región prestada del estado, sin el
  `.cloned()` que copiaba todos sus años (mismo patrón que `/api/zonas/{id}`).
- `?variable=`: `eq_ignore_ascii_case` en vez de `to_lowercase()`, que creaba un `String`
  por cada variable comparada.

## Pendiente
- Subir `rust-toolchain.toml` a mano cuando haga falta, en su propio PR.
- Si dependabot abre un PR de pip, el CI saldrá rojo hasta regenerar el lock con el comando
  de su cabecera (es lo esperado).
