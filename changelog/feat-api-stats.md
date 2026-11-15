# feat/api-stats

PR → `developer`. Cierra la tarea de `docs/api-stats.md` (#37).

## Añadido
- `/api/zonas` y `/api/zonas/{id}` devuelven `celdas`, `nota?` y `stats` (de `pipeline/tendencias.py`) tal cual: sin recalcular ni redondear `status`, `aviso` ni ningún número.
- `src/models/zona.rs`: `Zona`, `Stats` y `Status` (`real` · `posible_casualidad` · `pocos_datos`) con `deny_unknown_fields`.
- Tests en `tests/api.rs` (stats en las 25 zonas, aviso 2014 solo en lluvia, `pocos_datos` lleva `nota`, serie y stats del mismo periodo en las 50 fichas, JSON mal formados rechazados) y 3 comprobaciones en `tests/e2e.sh`.

## Cambiado
- `/api/variables` se lee de `data/variables.json` en vez de recalcularse. `anio_inicio`/`anio_fin` pasan a obligatorios.
- `CLAUDE.md`: también se embeben `variables.json` y `zonas/*.json`; tras regenerar `power.json`/`gpm.json` hay que correr `tendencias.py`.
- `Variable` ya no guarda unidad/fuente/descripción: salen de `variables.json` (una sola fuente).
- `Datos::desde_json(power, gpm)` → `Datos::desde(Fuentes)`. En los tests: `Fuentes { gpm: x, ..Fuentes::EMBEBIDAS }`.
- `openapi.json` regenerado: nuevos `Stats` y `Status`; `Zona`, `ZonaDetalle` y `VariableInfo` cambian.

## Decisión: opción A (3 JSON + serie desde `power.json`/`gpm.json`)
- Se embeben `data/variables.json` y `data/zonas/{lluvia,temperatura}.json` con `include_str!`, sin crates nuevos. No se usan los 50 `data/zonas/{variable}/{id}.json` (opción B, `include_dir`).
- Por qué: no añade dependencias, cambia menos código y el frontend recibe lo mismo.
- La serie se recorta a `year_start`–`year_end` de `stats` y se valida al arrancar (`n_years` puntos, del primer al último año). Si el cron añade años a `power.json`/`gpm.json`, la ficha sigue mostrando el periodo de la tendencia. Si los datos no cuadran, la API no arranca y el error dice qué zona falla.
- También se valida al arrancar:
  - 25 zonas por variable, ids `01`–`25` en orden y con el nombre de su ubigeo (`ubigeo::UBIGEOS`).
  - El periodo de `stats` de cada zona cabe en el de `variables.json` (cada zona puede tener el suyo, como en `tendencias.py`).
  - `lat`, `lon`, `celdas` y `nota` coinciden con `power.json`/`gpm.json`, así `/api/*` y `/power`, `/gpm` no se contradicen.

## Quitado
- `schema::Zona` (lo sustituye `models::zona::Zona`), `Datos::nota()`, `Datos::serie()`, `ubigeo::de_nombre` y `ubigeo::nombre`, que ya no se usaban.
- Los tests cargan los datos una sola vez (`LazyLock`).

## Para el frontend
- Regenerar los tipos (`pnpm gen`) con el `openapi.json` nuevo.
- `aviso` (cuidado al interpretar la tendencia) y `nota` (pocas celdas de la fuente) son cosas distintas: mostrar las dos.
