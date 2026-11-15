# chore/correcciones-review-back

Las 7 mejoras de la review de `main...developer` (#45–#48). Sin cambios de contrato:
`openapi.json`, rutas y forma de las respuestas siguen igual.

## CI y workflows
- `ci.yml`: nuevo paso que regenera `pipeline/requirements.lock` con `uv` (versión fija
  `0.13.8`) y falla si difiere de lo commiteado. Parte del lock actual, así que las
  transitivas conservan su pin y solo cuenta lo que cambia `requirements.txt`. Corre antes
  del `pip install` para fallar rápido. dependabot solo actualiza `requirements.txt`; antes
  el CI salía verde probando las versiones viejas del lock.
- `actualizar-datos.yml`: `gh pr create` ya no se traga los errores con `|| echo`; si falla,
  el job queda en rojo con el error real.
- `actualizar-datos.yml`: fuera `git push --force`. Si la rama del día ya existe, git
  rechaza el push y no se pisa nada: si ya tiene PR, el job falla con un mensaje claro; si
  quedó sin PR (un `gh` fallido antes), abre el PR con la rama ya subida.
- `rust-toolchain.toml`: Rust fijado en `1.99.0` (con `rustfmt` y `clippy`). Una estable
  nueva con lints nuevos ya no pone el CI en rojo sin tocar código.

## Rendimiento de la API
- `GET /api/openapi.json`: sirve el `openapi.json` de la raíz embebido con `include_str!`,
  en vez de reconstruir y serializar utoipa en cada petición. El test
  `openapi_json_esta_al_dia` garantiza que es idéntico al generado.
- `/power/{region}` y `/gpm/{region}`: se serializa la región prestada del estado, sin el
  `.cloned()` que copiaba todos sus años (mismo patrón que `/api/zonas/{id}`).
- `?variable=`: `eq_ignore_ascii_case` en vez de `to_lowercase()`, que creaba un `String`
  por cada variable comparada.

## Pendiente
- Subir `rust-toolchain.toml` a mano cuando haga falta, en su propio PR.
- Si dependabot abre un PR de pip, el CI saldrá rojo hasta regenerar el lock con el comando
  de su cabecera (es lo esperado).
