# feat/ndvi-api

PR: base `feat/pipeline-ndvi` (#42, de Josue), a pedido del equipo: el JSON y el endpoint van aparte. Autor: Favio.

## Añadido
- **`data/ndvi.json`**, con Chavimochic (ubigeo 13) e Ica-Villacurí (11), 2001–2024. Se generó con `pipeline/ndvi.py calcular` a partir de los NetCDF de la solicitud AppEEARS del Lab 3 (mismas cajas), así que no hizo falta otra solicitud de ~3 h.
- **`GET /api/vegetacion`:** las zonas tal cual están en el archivo, con `unidad_geografica`, `bbox`, `serie: [{anio, ndvi_anual, area_verde_km2}]` (la misma forma de lista que `/api/zonas/{id}`, no un mapa por año) y `stats` (con `status` y, si lo hubiera, `aviso`). La API no recalcula ni redondea.
  - Modelo: `src/models/vegetacion.rs` (`ZonaVegetacion`, `AnioVegetacion`), con `deny_unknown_fields`. Reutiliza `Stats` de `zona.rs`.
  - Validación al arrancar (`src/data.rs`): zonas no vacías e ids únicos; ubigeo existente y departamento correcto; `unidad_geografica` presente; `lat`/`lon` dentro del `bbox`; NDVI entre −1 y 1 y área ≥ 0; años de `serie` ordenados, sin repetir y = periodo y `n_years` de `stats`. El error dice qué zona falla.
  - Tests en `tests/api.rs`: el endpoint devuelve las 2 zonas, `real`, con los valores 2001 y 2024 del Lab 3; 12 roturas de `ndvi.json` impiden arrancar.
  - Contrato: `openapi.json` regenerado (`UPDATE_OPENAPI=1 cargo test openapi`). Después, en el frontend: `pnpm gen`.

## Cambios tras la revisión (15 nov)
- **`serie` en vez de `anios`:** lista ordenada `[{anio, ndvi_anual, area_verde_km2}]`, consistente con `/api/zonas/{id}`. Cambian `pipeline/ndvi.py`, `data/ndvi.json`, el modelo, la validación, `checks_ndvi.sh`, las pruebas y `openapi.json`.
- **p y q nunca valen 0:** `clasificar()` publica como mínimo `0.000001` (`P_MIN` en `tendencias.py`); la ficha muestra «< 0,000001». `data/zonas` no cambia (ningún valor redondeaba a 0); sí `ndvi.json`.
- Merge de `feat/pipeline-ndvi` (#42): este PR no traía los 3 últimos commits (`.dt` en `_leer_zona`, `.venv` en el e2e, changelog).
- Fecha de `docs/vegetacion.md` puesta al día de la revisión (2026-11-15).

## Comprobado contra el Lab 3
| Zona | NDVI 2001 → 2024 | Área verde 2001 → 2024 | Tendencia |
|---|---|---|---|
| Chavimochic | 0,1906 → 0,3104 | 188,9 → 355,5 km² | +0,0535/déc, IC [0,0467; 0,0612], real |
| Ica-Villacurí | 0,1403 → 0,198 | 117,6 → 221,5 km² | +0,0273/déc, IC [0,0247; 0,0294], real |

## Corregido
- `pipeline/ndvi.py calcular` fallaba con `requirements.txt`: las fechas de AppEEARS vienen en calendario juliano y xarray necesita `cftime`. Se añadió `cftime==1.6.6.1` a `requirements.txt` y se regeneró `requirements.lock` con `uv` (Python 3.12, Linux, con hashes; solo entra `cftime`).
- `ndvi.py` busca también `~/_netrc`, que es como earthaccess guarda la credencial en Windows.

## Docs
- `README.md`: fila de `/api/vegetacion`.
- `CLAUDE.md`: `ndvi.json` se embebe.
- `docs/vegetacion.md`: el «Pendiente» pasa a «En la API».

## Pendiente
- Mezclar después de #42. Si #42 se mezcla primero y borra su rama, GitHub cambia la base de este PR a `developer`.
- Frontend: `pnpm gen` y mostrar las cifras del Caso 2 desde `/api/vegetacion`, con su `unidad_geografica`.
- Selva (MOD44B) y Olmos: PR aparte (parte 2 de la tarea).
- En Windows, `tests/test_ndvi_checks.py` falla si no está `jq` (lo usa `checks_ndvi.sh`); en el CI sí está.
