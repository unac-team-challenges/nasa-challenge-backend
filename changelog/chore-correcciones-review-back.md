# chore/correcciones-review-back

Las 7 mejoras de la review de `main...developer` (#45–#48). Sin cambios de contrato:
`openapi.json`, rutas y forma de las respuestas siguen igual.

## CI y workflows
- `ci.yml`: nuevo paso, el primero del job, que regenera `pipeline/requirements.lock` con
  `uv` (versión fija `0.13.8`) y falla si los pins (`paquete==versión`) difieren de lo
  commiteado. Parte del lock actual, así que las transitivas conservan su pin y solo cuenta
  lo que cambia `requirements.txt`; no compara hashes ni formato, que pueden variar sin
  cambios en el repo. dependabot solo actualiza `requirements.txt`; antes el CI salía verde
  probando las versiones viejas del lock.
- `actualizar-datos.yml`: `gh pr create` ya no se traga los errores con `|| echo`; si falla,
  el job queda en rojo con el error real.
- `actualizar-datos.yml`: fuera `git push --force`. Si la rama del día ya existe (otra
  ejecución el mismo día), git rechaza el push, no se pisa nada y el job falla con un
  mensaje claro: mezclar o cerrar su PR, borrar la rama y relanzar.
- `actualizar-datos.yml`: la fecha se calcula una vez (`hoy`), así rama y título del PR
  coinciden aunque el job cruce medianoche.
- `rust-toolchain.toml`: Rust fijado en `1.99.0` (con `rustfmt` y `clippy`). Una estable
  nueva con lints nuevos ya no pone el CI en rojo sin tocar código.

## Rendimiento de la API
- `GET /api/openapi.json`: el documento se genera una sola vez (`LazyLock`) y se sirve como
  `&'static str`, en vez de reconstruir y serializar utoipa en cada petición. Se sigue
  generando desde el código, así que no puede desfasarse de las rutas, y se fuerza al montar
  el router: un fallo se ve al arrancar.
- `Region` y `Medidas` (power, gpm) ya no derivan `Clone`: volver a copiar los años sería un
  error de compilación.
- `/power/{region}` y `/gpm/{region}`: se serializa la región prestada del estado, sin el
  `.cloned()` que copiaba todos sus años (mismo patrón que `/api/zonas/{id}`).
- `?variable=`: `eq_ignore_ascii_case` en vez de `to_lowercase()`, que creaba un `String`
  por cada variable comparada. Nuevos tests `api_variable_ignora_mayusculas_y_espacios` e `ids_de_variable_son_ascii`.

## Docs
- `README.md`: `pip install uv==0.13.8`, la misma versión que el CI.
- `docs/propuestas-mejora/README.md`: `rust-toolchain.toml` ya no figura como pendiente.

## Pendiente
- Subir `rust-toolchain.toml` a mano cuando haga falta, en su propio PR.
- Si dependabot abre un PR de pip, el CI saldrá rojo hasta regenerar el lock con el comando
  de su cabecera (es lo esperado).
