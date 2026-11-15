# feat/pipeline-ndvi

PR: base `developer`. Tareas A y B de la nota del equipo (`15-tareas-josue-vegetacion-14nov.md`).

## Añadido
- `pipeline/tendencia_comun.py`: el criterio único de «tendencia real» en un solo lugar (`evaluar()`).
- `pipeline/ndvi.py`: vegetación MODIS MOD13A3 v061 → `data/ndvi.json` (Chavimochic e Ica-Villacurí). Pasos `enviar`, `estado`, `bajar`, `calcular` y `autoprueba`. Mismo método que la temperatura (`estadisticas()` + `clasificar()`).
- `tests/e2e.sh`: compila `ndvi.py`, corre las autopruebas de `ndvi.py` y `lab5`, valida `data/ndvi.json` si existe (series, años, `stats`, criterio, unidad geográfica) y avisa si falta.
- `.gitignore`: `pipeline/cache/` (NetCDF y `task.json` de AppEEARS).
- `docs/vegetacion.md`: cómo se calcula la variable y propuesta para la selva (MOD44B, cobertura de árboles).

## Corregido
- **Criterio único** (`docs/tendencias.md` §2b): `real` solo con `q < 0.05`, IC95 sin 0 y `|lag1| <= 0.5`. Antes `tendencias.py` y `lab5.main()` decidían solo con `q`.
- `data/zonas/temperatura*`: Loreto (IC cruza 0) y Huánuco (`lag1` 0,54) pasan a `posible_casualidad`: 13 → 11 `real`. Regenerado con `python pipeline/tendencias.py`.
- `aviso` explica por qué una tendencia significativa no es `real` (IC con 0 o `|lag1|` alto). Antes, con `lag1` negativo bajaba el estado sin aviso.
- `power_departamentos.py` (lab) reutiliza `estado()` de `lab5`: 0 diferencias en sus 200 filas publicadas.

## Revisión
La primera revisión independiente de lo pedido se interrumpió (límite de uso) y el PR se abrió sin ella. La revisión completa encontró, entre otros: la afirmación falsa de que todos los bloques se podían quitar por separado, `aviso` y `status` inconsistentes con `lag1` negativo, la doc prometía un «motivo» que el código no escribía, `ndvi.py` con el mínimo de años del lab (10 en vez de 20) y otro método que el del producto, un check de `jq` del e2e que fallaba con un JSON válido, y pruebas que no detectaban regresiones. Todo corregido en los commits `fix:` y `docs:` posteriores al primer push.

## Pruebas
- `tests/test_tendencias.py`: 9 pruebas, en verde con las dependencias reales.
- `python pipeline/ndvi.py autoprueba`: detecta 3 mutaciones introducidas a propósito (sin filtro de años, contar entradas en vez de meses, sin mínimo de 20 años).
- Checks de `ndvi.json` en el e2e: pasan con un JSON válido y fallan con 6 roturas distintas.
- Comparación `lab5` frente a `pymannkendall`/`scipy` repetida sobre las 50 series de `data/`: p idéntico, IC hasta 0,0047 por década, ninguna cambia de lado del 0.

## Pendiente
- **`data/ndvi.json` y el endpoint de la API.** La solicitud a AppEEARS dio `401`: la credencial Earthdata local no es válida. Con una credencial válida: `python pipeline/ndvi.py enviar`, ~3 h, `bajar`, `calcular`. Comprobar que 2001 y 2024 coinciden con el Lab 3.
- `pipeline/exploracion/josue/resultados/lab5_tendencias.csv` sigue con la regla vieja (solo `q`): su entrada `salida/lab1_power_anual.csv` no está en el repo. Es un resultado del lab, no lo lee el producto.
- `cargo fmt`: `developer` no pasa `cargo fmt --check`; formatear en un PR aparte.
- Selva: decidir si se usa MOD44B.

## Además: pipeline más robusto (propuestas 5 y 6 de `docs/propuestas-mejora/`)

Se agregó a este PR para dejar en uno solo todo lo avanzado en local:

- **`power.py` reintenta** con `urllib3.Retry`: 4 intentos con espera creciente ante 429/500/502/503/504. Antes, un 503 pasajero tumbaba las 16 llamadas.
- **Avisos de años descartados** por `stderr`, en `power.py` y `gpm.py`: qué año no entra y en qué regiones. Un año que falta cambia la pendiente y `n_years`, y debe verse en el log.
- **`gpm.py` incremental:** no vuelve a pedir los años que ya están completos en las 25 regiones de `data/gpm.json`. IMERG v07 está congelado desde sep 2025: sin esto, el cron mensual pedía todo para obtener el mismo resultado. `--todo` fuerza la descarga completa.
- **`tests/test_pipeline.py`:** 4 pruebas sin red, incluido en el e2e. Detecta la mutación de cambiar la intersección de años por la unión.

## Además: más pruebas y pendientes cerrados

- **Los checks «sin null/NaN» no detectaban `NaN`.** `jq` lee `NaN` como número, así que `all(type == "number")` lo dejaba pasar en `power.json`, `gpm.json`, `zonas` y `ndvi.json`. Ahora exigen además `(isnan | not)`. Probado con un `power.json` con `NaN`: ya no pasa.
- **Checks de `ndvi.json` probados aunque el archivo no exista todavía:**
  - salen a `tests/checks_ndvi.sh`, y el e2e los llama cuando el archivo existe;
  - `tests/test_ndvi_checks.py` arma un ejemplo con las funciones de `pipeline/ndvi.py`;
  - confirma que el ejemplo pasa y que cada una de 7 roturas se detecta: null, NaN, NDVI fuera de rango, año fuera de 2001–2024, status inválido, «real» sin criterio y sin unidad geográfica;
  - así quedó en el repo la prueba que antes se hizo a mano.
- **`lab5_tendencias.csv` del lab regenerado con el criterio único.** Su entrada se volvió a bajar de NASA POWER.
  - Las 40 series dan las mismas pendientes.
  - Iquitos (lluvia 1981–2024) pasa de `real` a `posible_casualidad` por `lag1` = 0,74.
  - Se agrega la columna `motivo`.
- **Pendientes cerrados:**
  - el choque con #34 ya no existe (se cerró);
  - `cargo fmt` lo hizo #46.

## Revisión de Leandro (14 nov)

| Punto | Respuesta |
|---|---|
| `t.year` falla con fechas `datetime64` en `_leer_zona` | Corregido: `ds["time"].dt.year` y `.dt.month` sirven con `datetime64` y con `cftime`. Una prueba con un NetCDF sintético reproducía el `AttributeError` antes del arreglo |
| El e2e usa el `python3` del sistema y falla en local sin las dependencias | Ahora usa `.venv/bin/python` si existe; el CI no cambia |
| Falta `data/ndvi.json` y el endpoint | Los trae **#50** (Favio), hecho sobre esta rama: con los NetCDF reales del Lab 3, coincide con el Lab 3 y agrega `GET /api/vegetacion`. La credencial de Earthdata ya funciona (AppEEARS responde 200), por si hay que volver a pedir los datos |
| Choque con #34 | #34 se cerró: ya no hay conflicto |
| `lab5_tendencias.csv` con la regla vieja | Regenerado en este PR (ver «Más pruebas») |
| «Un PR = un tema» | La tarea A se cierra con #50 encima de este PR, como acordó el equipo |
