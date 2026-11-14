# feat/datos-desde-2000

## Cambiado
- `data/power.json`: 2000–2025 (26 años × 25 regiones; `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`).
- `data/gpm.json`: 2000–2024 (25 años × 25 regiones, `lluvia_mm_dia`). El 2025 queda fuera porque IMERG no tiene los 12 meses (regla de años completos).
- `actualizar-datos.yml` y los valores por defecto de `power.py`/`gpm.py`: inicio 2000 (antes 2015).
- Docs: `README.md`, `CLAUDE.md`, `docs/guia-pipeline.md`, `docs/datos.md` y `docs/reglas-datos.md` con el periodo nuevo.

## Notas
- Sin `NaN`, ninguna región con años vacíos; los valores de 2015–2020 no cambiaron.
- El Drive (`06`/`13`) dice que IMERG empieza en jun 2000 y propone 2001–2024. La búsqueda en Earthdata devuelve los 12 meses de 2000 para `GPM_3IMERGM` v07, así que se usa 2000.
- Los JSON se embeben al compilar: la API necesita recompilarse/redesplegarse para servir los años nuevos.
