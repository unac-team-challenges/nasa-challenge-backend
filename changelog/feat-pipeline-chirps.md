# feat/pipeline-chirps

PR: #11, base `feat/pipeline-gpm` (#9); pasa a `developer` cuando #9 se mezcle.

## Añadido
- `pipeline/chirps.py`: lluvia de CHIRPS v2.0 mensual (~5 km, sin cuenta) como segunda opinión de GPM. Lee los COG de `data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/cogs/` a distancia con `rasterio`: solo baja los píxeles de las capitales. mm/mes ÷ días del mes = `lluvia_mm_dia`.
- `data/chirps.json`: 2015–2020, 25 regiones, misma forma que `data/power.json`.
- Workflow mensual: corre `chirps.py`.
- `tests/e2e.sh`: valida `data/chirps.json` (25 regiones, sin null/NaN) y que `chirps.py` compile.
- `pipeline/requirements.txt`: `rasterio`.

## Corregido (revisión de #11)
- `allow_nan=False` y solo años completos (12 meses válidos). El píxel de mar (`-9999`) ya no puede producir `NaN`; un año aún no publicado se omite.

## Notas
- En la costa, GPM y CHIRPS no coinciden en el píxel de la capital (2017: Piura 2,60 frente a 0,33; Ica 0,29 frente a 1,38; Lambayeque 1,14 frente a 0,03 mm/día). En la sierra y la selva coinciden bastante. Argumento para usar el promedio del departamento.
- Existe CHIRPS v3.0; cambiarla es solo cambiar la URL.
