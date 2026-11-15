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
