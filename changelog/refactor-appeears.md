# refactor/appeears

Punto 1 de lo que dejó Leandro al mezclar el #57 (revisión del #55). Es un refactor: los JSON no cambian.

## Qué cambia
- **`pipeline/appeears.py` (nuevo):** lo común de AppEEARS, que estaba copiado en `ndvi.py` y `cobertura.py`:
  - `credenciales()` y `token()`;
  - `enviar(zonas, producto, capas, anios, task, nombre)`, `estado()` y `consultar()`;
  - `bajar(task, destino_dir)`, la versión segura de `cobertura.py` (descarga a `.part`, limpia `.part` huérfanos, no toca la caché si el bundle no trae `.nc` y reemplaza los `.nc` solo al final);
  - `nc_de_zona(cache, zona)`, el NetCDF cuyo centro cae en la caja de la zona.
- **`ndvi.py` y `cobertura.py`:** `enviar`, `consultar` y `bajar` quedan como envoltorios de una línea con su producto, capas, zonas y caché. `_leer_zona` usa `appeears.nc_de_zona`. Los comandos (`enviar|estado|bajar|calcular|autoprueba`) y `lab3_olmos.py` funcionan igual.
- **`escribir`:** ndvi y cobertura usan `tendencias.escribir(ruta, filas, salto_final=True)`. Es el único escritor de `data/*.json`; `salto_final` mantiene el salto de línea final que ya tenían sus archivos.
- `tests/e2e.sh` compila `pipeline/appeears.py`; `docs/vegetacion.md` lo menciona.

## Único cambio de comportamiento
`ndvi.py bajar` ahora usa la descarga segura. Antes borraba los `.nc` de la caché **antes** de bajar, así que un corte dejaba la caché vacía. Solo cambia cuando la descarga falla.

También: si el bundle no trae ningún `.nc`, `ndvi.py bajar` ahora termina con error y conserva la caché (antes la dejaba vacía sin avisar).

## Comprobado
- `python pipeline/ndvi.py calcular`, `python pipeline/cobertura.py calcular` y `python pipeline/tendencias.py`: `git status data/` vacío. `ndvi.json`, `cobertura_arboles.json`, `variables.json` y `zonas/` salen **idénticos byte a byte**.
- Autopruebas de ndvi y cobertura, y `tests/test_pipeline.py` (`_leer_zona` con un NetCDF sintético): OK.
- `bajar` con AppEEARS simulado (sin red): la descarga normal reemplaza el `.nc` viejo y limpia el `.part` huérfano; sin ningún `.nc` conserva la copia; un corte a media descarga conserva la copia y no deja `.part`.

## Pendiente del #57
Este PR cierra solo el punto 1. Siguen pendientes el punto 2 (simplificar los recuadros de `src/data.rs` con un `ZonaRecuadro<A>` genérico) y el punto 4 (frontend: `pnpm gen` y la ficha de la selva).
