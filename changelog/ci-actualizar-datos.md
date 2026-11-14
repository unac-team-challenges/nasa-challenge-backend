# ci/actualizar-datos

PR: #6 → `developer`

## Añadido
- Workflow mensual (`.github/workflows/actualizar-datos.yml`) que regenera `data/power.json`.
- CORS para `localhost` y `127.0.0.1` en la API (`tower-http`).
- `numpy` en `pipeline/requirements.txt`.

## Corregido
- `pipeline/power.py`: solo años completos y `allow_nan=False`; un `NaN` ya no puede romper el arranque de la API.

## Notas
- Lima y Callao comparten celda en NASA POWER (datos idénticos); se deja así.
- Pendiente: añadir la URL de Vercel a `origen_permitido` y decidir cuándo el workflow apunta a `main`.
