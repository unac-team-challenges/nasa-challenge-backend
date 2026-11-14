# feat/pipeline-promedio-departamento

PR → `developer`. Sigue la sección 3b de `docs/reglas-datos.md` y la sección 6 de `docs/tendencias.md`: unidad geográfica = promedio del departamento.

## Cambiado
- `gpm.py`: cada valor es el **promedio de todas las celdas de IMERG del departamento**, no el píxel de la capital. Periodo 2001–2024. Pide por OPeNDAP solo el recorte de Perú de cada mes (~60 KB en vez de 18 MB, en memoria, 4 en paralelo): 2001–2024 en ~3,5 min, con los mismos valores que el archivo completo.
- `power.py`: API **regional** de POWER en 4 recuadros (máximo 10° por lado), igual que `pipeline/exploracion/josue/scripts/power_departamentos.py`, y promedio por departamento. Periodo 1981–2024. Un año entra solo si las 4 variables lo tienen completo.
- `data/gpm.json` y `data/power.json` regenerados.
- Workflow mensual: POWER desde 1981 y GPM desde 2001.

## Añadido
- `pipeline/departamentos.py`: máscara de los 25 departamentos con `regionmask` (una celda pertenece al departamento que contiene su centro), `UBIGEO` y `a_json()` compartido.
- `pipeline/geo/peru_departamentos.geojson` (`juaneladio/peru-geojson`, MPL-2.0, 140 KB).
- **Aviso de contrato:** dos campos nuevos por región en `power.json` y `gpm.json`: `celdas` (cuántas entran en el promedio) y `nota` (si hay menos de 4 celdas). `anios` no cambia de forma.
- `pipeline/requirements.txt`: `geopandas`, `regionmask`.

## Quitado
- CHIRPS (`chirps.py`, `data/chirps.json`), descartado por el equipo en #11.

## Notas
- Las celdas por departamento coinciden con la tabla del lab 4. IMERG: Callao 1, Tumbes 37, Loreto 3054. POWER: Callao 0, Tumbes 1, Lambayeque 3.
- Callao no tiene celdas propias en POWER: usa la celda de su capital (compartida con Lima) y lleva `nota`. Se respeta la decisión "Lima y Callao tal cual".
- `lat` y `lon` siguen siendo la capital (punto del mapa).
- Al unir `developer` (#20, "datos desde 2000") chocaron los periodos: se mantienen los de este PR (POWER 1981–2024, GPM 2001–2024) y se ajustaron README, CLAUDE.md y docs. `changelog/feat-datos-desde-2000.md` queda como historial de #20.
- Al unir `developer` con #24 (`deny_unknown_fields`), `celdas` y `nota` pasan a ser parte del modelo `Region` (`celdas` obligatorio, `nota` opcional) y salen en `/power/{region}` y `/gpm/{region}`. Test nuevo: Callao lleva `celdas` y `nota`; Lima no lleva `nota`.
