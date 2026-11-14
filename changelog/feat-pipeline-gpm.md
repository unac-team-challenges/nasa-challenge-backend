# feat/pipeline-gpm

PR: #9 → `developer`

## Añadido
- `pipeline/gpm.py`: lluvia de GPM IMERG mensual v07 (`GPM_3IMERGM`) con `earthaccess`. Baja un mes a la vez (~18 MB), lo lee y lo borra; reintenta si GES DISC falla. Celda más cercana a la capital de cada región (`REGIONES` de `power.py`), mm/hr × 24 = `lluvia_mm_dia`.
- `data/gpm.json`: 2015–2020, 25 regiones, misma forma que `data/power.json`.
- Workflow mensual: corre `gpm.py` con `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` como secrets.
- `tests/e2e.sh`: valida `data/gpm.json` (25 regiones, sin null/NaN) y que `gpm.py` compile.
- `pipeline/requirements.txt`: `earthaccess`, `python-dotenv`, `xarray`, `h5netcdf`, `h5py`.

## Corregido (revisión de #9)
- `allow_nan=False` y solo años completos (12 meses válidos), igual que `power.py`. Así el año en curso del cron nunca entra incompleto.

## Decisión (2026-11-14)
- Lluvia del producto = **GPM IMERG**; CHIRPS (#11) se descarta. Registrado en `docs/reglas-datos.md` (sección 3b). Se mezcló `developer` en la rama para traer ese archivo.

## Pendiente
- Guardar los secrets de Earthdata en el repo. La cuenta debe tener aceptados los términos de "NASA GESDISC DATA ARCHIVE"; si no, GES DISC responde 403 "EULA Acceptance Failure".
- Decidir si se usa la capital o el promedio del departamento (ver comentario en #9 y el hallazgo de la costa en #11).

## Notas
- IMERG sobreestima la lluvia en el desierto costero (Lima, Ica, Tacna: ~0,2–0,3 mm/día, unos 100 mm/año).
