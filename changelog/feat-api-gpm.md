# feat/api-gpm

## Añadido
- `GET /gpm/{region}`: lluvia anual GPM IMERG (`lluvia_mm_dia` por año), con la misma forma, búsqueda sin tildes y 404 JSON que `/power/{region}`.
- `src/models/gpm.rs`; `models::Region<M>` genérico (forma común de los `data/*.json`) y `Datos` carga también `data/gpm.json`.
- Tests en `tests/api.rs` y comprobaciones en `tests/e2e.sh`.

## Notas
- `Datos::desde_json` recibe ahora `(power, gpm)`.
- El endpoint refleja los años que tenga `data/gpm.json`; la ampliación a 2000–2025 va en otra rama (`feat/datos-desde-2000`).
