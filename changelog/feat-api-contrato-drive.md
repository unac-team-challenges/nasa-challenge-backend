# feat/api-contrato-drive

Base: `feat/api-gpm` (#16). Mezclar #16 primero.

## Añadido
- Rutas del contrato del Drive (`07-stack-decidido`): `GET /api/variables`, `GET /api/zonas?variable=`, `GET /api/zonas/{id}?variable=`.
- `id` de zona = ubigeo como texto (`"01"`–`"25"`; `"07"` Callao, `"15"` Lima), tabla en `src/ubigeo.rs`.
- Variables `lluvia` (GPM IMERG) y `temperatura` (`T2M`, MERRA-2 vía POWER) en `models/variable.rs`.
- `variable` obligatoria: 400 JSON si falta o no existe; 404 JSON si el ubigeo no existe.
- Tests en `tests/api.rs` y `tests/e2e.sh`; README actualizado.

## Pendiente
- `stats` (tendencia: `slope_per_decade`, `q_value`, `status`…): lo calcula el pipeline de tendencias de Sebastian (`docs/tendencias.md`); hasta entonces la ficha solo trae la serie.
- `/api/casos/{id}` y `/api/hallazgos`: dependen de las tendencias.
- Decidir capital frente a promedio del departamento y si entran `T2M_MAX`/`T2M_MIN`.
- Las rutas `/power` y `/gpm` se mantienen.
