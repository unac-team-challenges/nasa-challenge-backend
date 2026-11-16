# feat/gpm-aviso-version

Avisa si CMR publica otra versión de `GPM_3IMERGM` además de la v07. Cierra el punto 3 de `docs/propuestas-mejora`.

## Añadido
- `pipeline/gpm.py`: `versiones_nuevas()` consulta CMR con `earthaccess.search_datasets(short_name="GPM_3IMERGM")` y devuelve las
  versiones distintas de `"07"`. En `__main__`, tras el login, imprime en stderr
  `AVISO: CMR publica GPM_3IMERGM versión X; v07 sigue siendo la que usamos (docs/reglas-datos.md)`.
  Si la consulta falla (red), avisa y sigue.
- `VERSION = "07"` como constante (antes estaba fija dentro de `anio_promedio`).
- `tests/test_pipeline.py`: tres pruebas con la búsqueda simulada (sin versiones nuevas, con `"08"`, sin red).

## No cambia
- La versión usada sigue siendo v07; nunca se mezcla con otra (`docs/reglas-datos.md`).
- `actualizar-datos.yml` no se toca (ni se quita `-W ignore`: exige lanzar el workflow después).

## Nota
`earthaccess` 0.19.0 no tiene `search_collections`; el equivalente es `search_datasets`, y `version` es una propiedad.

## Docs
- `docs/propuestas-mejora/02-pipeline-y-datos.md`: el paso 3 queda marcado como hecho.
