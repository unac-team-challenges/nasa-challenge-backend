# feat/pipeline-promedio-departamento

PR: base `feat/pipeline-chirps` (#11); pasa a `developer` cuando #9 y #11 se mezclen.

## Cambiado
- `gpm.py` y `chirps.py`: cada valor es el **promedio de todas las celdas del departamento**, no el píxel de la capital. Se aplica la regla 4 de `docs/reglas-datos.md` a los 25 departamentos, para que todo el mapa use el mismo método.
- `data/gpm.json` y `data/chirps.json` regenerados (2015–2020).

## Añadido
- `pipeline/departamentos.py`: máscara de los 25 departamentos con `regionmask` (una celda pertenece al departamento que contiene su centro) y `a_json()` compartido.
- `pipeline/geo/peru_departamentos.geojson` (`juaneladio/peru-geojson`, MPL-2.0, 140 KB).
- Campo `celdas` por región en `gpm.json` y `chirps.json`, y `nota` cuando el promedio usa menos de 4 celdas (Callao en GPM). **Aviso de contrato:** dos campos nuevos por región; `anios` no cambia de forma.
- `pipeline/requirements.txt`: `geopandas`, `regionmask`.

## Notas
- Celdas por departamento: iguales a la tabla del lab 4 (`pipeline/exploracion/lab4_departamentos.py`). IMERG: Callao 1, Tumbes 37, Loreto 3054.
- `lat` y `lon` siguen siendo la capital (punto para el mapa), no el centro del promedio.
