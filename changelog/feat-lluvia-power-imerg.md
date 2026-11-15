# feat/lluvia-power-imerg

PR: base `feat/pipeline-ndvi` (#42), porque usa su criterio único de tendencia. Autor: Favio.

## Por qué
Con la lluvia de IMERG, el mapa salía entero en «baja / posible casualidad»: IMERG baja en 25 de 25 departamentos por el cambio de satélites de 2014 (TRMM → GPM), no por el clima. Además, el plan B del frontend (NASA POWER) contradecía a la API en **13 de 24 departamentos** con el mismo periodo, 2001–2024 (Piura: IMERG −20 mm, POWER +11 mm; Puno: IMERG −91 mm, POWER +141 mm, real). Según por dónde se entraba a la web, el mismo departamento subía o bajaba.

Decisión de producto (Favio, 2026-11-15, opción C): **POWER como lluvia principal e IMERG como segunda fuente para comparar** («¿Coinciden dos fuentes de NASA?», del prototipo v4).

## Cambiado
- `pipeline/tendencias.py`: `lluvia` sale de `power.json` (`PRECTOTCORR`) con el criterio normal (puede ser `real`). Nueva variable `lluvia_imerg` (`gpm.json`), con el aviso de 2014 y nunca `real`. Orden: `lluvia`, `temperatura`, `lluvia_imerg`.
- `data/`: regenerados `variables.json` y `zonas/lluvia*`; nuevos `zonas/lluvia_imerg.json` y `zonas/lluvia_imerg/*.json`.
  - `lluvia` (POWER): 5 real, 17 posible casualidad, 3 pocos datos.
  - `lluvia_imerg`: 0 real, 24 posible casualidad, 1 pocos datos.
  - `temperatura`: sin cambios.
- Rust: `Variable::LluviaImerg` (`"lluvia_imerg"`, `serde` en `snake_case`). `lluvia` cruza su serie con `power.json` y `lluvia_imerg` con `gpm.json`. Mensajes de error con las 3 variables. `openapi.json` regenerado.
- Tests:
  - `tests/api.rs`: las 3 variables en los recorridos.
  - Test nuevo `lluvia_power_puede_ser_real_e_imerg_nunca`.
  - El aviso de 2014 pasa a `lluvia_imerg`, y la nota de Lambayeque depende de la fuente.
  - `tests/test_tendencias.py` y `tests/e2e.sh` adaptados.
- Docs: `reglas-datos.md` §3b, `tendencias.md`, `README.md` y `CLAUDE.md`.

## Contrato
- `/api/zonas?variable=lluvia` mantiene la forma de siempre, pero cambia su fuente. `/api/variables` trae una tercera entrada, `lluvia_imerg`. **El frontend tiene que filtrar `lluvia_imerg` del selector** (va en su propio PR).

## Pendiente
- Que el equipo (Josue, Leandro) acuerde el cambio de la regla 3b: cambia la decisión del 2026-11-14.
- Frontend: `pnpm gen`, plan B idéntico a la API (POWER + IMERG) y el bloque «¿Coinciden dos fuentes de NASA?» en la ficha.
- Lluvia larga (1981–2024) con POWER: posible, pero es otra decisión (power.json hoy empieza en 2001).
