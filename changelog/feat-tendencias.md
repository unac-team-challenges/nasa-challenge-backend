# feat/tendencias

PR → `developer` (rebasada sobre `developer` con la #22 y la #26 ya mezcladas). Sigue `docs/tendencias.md`.

## Añadido
- `pipeline/tendencias.py`: por zona y variable, sobre la serie anual del promedio del departamento:
  - Mann-Kendall con TFPW (`pymannkendall`) → `p_value`;
  - pendiente de Sen e IC 95 % (`scipy.stats.theilslopes`) ×10 → por década;
  - Benjamini-Hochberg entre las 25 zonas (`statsmodels`) → `q_value`;
  - `lag1` sin tendencia (como lab5 de Josue).
- Fuentes (regla 3b): **lluvia = IMERG** (`data/gpm.json`, `lluvia_mm_dia`) y **temperatura = POWER** (`data/power.json`, `T2M`). Periodo **2001–2024 para las dos** (`PERIODO` en el script): aunque el cron añada años a los JSON de entrada, las tendencias no cambian de periodo.
- Archivos del contrato del Drive (`07`), uno por ruta:
  - `data/variables.json`;
  - `data/zonas/{lluvia,temperatura}.json` (25 zonas con `stats`, sin serie);
  - `data/zonas/{variable}/{id}.json` (serie + `stats`).
  `id` = ubigeo `"01"`–`"25"`. Mismos campos base que `src/schema.rs` (`id`, `nombre`, `lat`, `lon`, `serie: [{anio, valor}]`), más `celdas` y `nota` copiados de la entrada.
- `stats`: `slope_per_decade`, `intercept`, `ci_low`, `ci_high`, `p_value`, `q_value`, `n_years`, `lag1`, `status`, `year_start`, `year_end`, más `pct_change_per_decade` (solo lluvia) y `aviso` (texto).
- `aviso`: **en las 25 zonas de lluvia**, porque IMERG cambia de constelación de satélites en 2014 (TRMM → GPM) y la tendencia puede estar sesgada a la baja; y en cualquier zona si `lag1 > 0.5`. Si hay los dos motivos, van en el mismo texto.
- `tests/test_tendencias.py` (unittest): semáforo y sus bordes, `status` coherente con el `q_value` publicado, `aviso`, recta de Sen reconstruible, `lag1` con años salteados y recorte a 2001–2024. Lo corre `tests/e2e.sh`.
- `tests/e2e.sh`: ids 01–25, `stats` numéricos sin null/NaN, `status` válido, 25 fichas por variable, periodo 2001–2024 en todas las zonas, lluvia de IMERG y `aviso` de 2014 en las 25 zonas de lluvia.
- `pipeline/requirements.txt`: `scipy==1.18.1`, `pymannkendall==1.4.3`, `statsmodels==0.15.0` (versión fija, como las demás).
- Workflow mensual: corre `tendencias.py` después de POWER y GPM y sube todo `data/` (también los archivos nuevos: usa `git status --porcelain`).
- CI (`ci.yml`): instala Python y `pipeline/requirements.txt` para poder correr `tests/test_tendencias.py`.

## Decisiones
- Semáforo (umbrales de Josue): `pocos_datos` si `n_years < 20` o `celdas < 4`; `real` si `q_value < 0.05`; si no, `posible_casualidad`. Documentado en `docs/tendencias.md` §6.

## Resultado (2001–2024)
- Lluvia: 15 `real`, 9 `posible_casualidad`, 1 `pocos_datos` (Callao).
- Temperatura: 13 `real`, 9 `posible_casualidad`, 3 `pocos_datos` (Callao, Lambayeque y Tumbes: menos de 4 celdas POWER).

## Notas
- `intercept` va con el año real: `valor = intercept + slope_per_decade / 10 × año`. Por eso los dos van con 6 decimales.
- Benjamini-Hochberg usa los `p_value` sin redondear; el `status` se decide con el `q_value` publicado.
- `unidad`, `fuente` y `descripcion` usan el mismo texto que `src/models/variable.rs`.
- No toca la API en Rust: servir `data/zonas/*` y `stats` lo hace Leandro después de esta PR.

## Pendiente
- GPCP solo como contraste de la lluvia, en una PR siguiente (no como fuente de la ficha).
