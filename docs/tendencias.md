# Cálculo de tendencias (para Sebastian)

**Tarea de Sebastian:** pendiente de Sen, Mann-Kendall y el resto de `stats` por zona y variable. Lo que hay hecho, qué falta calcular y cómo debe quedar. Fuente de las decisiones: Drive (`07-stack-decidido`, `13-datos-unificado-14nov`, `06-datos-a-usar`) y [`reglas-datos.md`](reglas-datos.md). **Los campos de tendencia están en progreso: lo marcado «por confirmar» lo decide el equipo/Sebastian.**

## 1. Qué tenemos (entrada)

Dos JSON en `data/`, generados por `pipeline/` (la API nunca calcula en vivo). Misma forma:

```json
[{"region": "Lima", "lat": -12.05, "lon": -77.04,
  "celdas": 9,
  "anios": {"2017": {"PRECTOTCORR": 0.155, "T2M": 18.5375, "T2M_MAX": 24.3633, "T2M_MIN": 14.0408}}}]
```

`celdas` = cuántas celdas de la malla entran en el promedio del departamento. Si son menos de 4 aparece también `nota` (texto): Callao, Tumbes y Lambayeque en POWER; Callao en GPM. **Copia la `nota` a tu salida** para que la ficha avise.

| Variable del producto | Archivo | Campo | Unidad | Fuente | Periodo |
|---|---|---|---|---|---|
| **Lluvia** | `data/gpm.json` | `lluvia_mm_dia` | mm/día | GPM IMERG v07 (NASA, ~10 km) | **2001–2024** (IMERG v07 existe de 1998 a sep 2025: el 2025 nunca estará completo; ver `reglas-datos.md` §3b) |
| **Temperatura** | `data/power.json` | `T2M` (+ `T2M_MAX`, `T2M_MIN`) | °C | MERRA-2 vía POWER (~50 km) | **2001–2024** (mismo periodo que la lluvia; POWER llega a 1981 pero se decidió usar 2001) |
| Lluvia POWER | `data/power.json` | `PRECTOTCORR` | mm/día | POWER | solo referencia, **no** va a la ficha |

- Ya vienen **promediados por año** y solo con **años completos (12 meses)**. Nunca `NaN`.
- **Unidad = promedio del departamento** (decidido y ya implementado en `pipeline/departamentos.py`): calcula las tendencias sobre estos JSON tal cual, sin volver a promediar. `lat`/`lon` son solo el punto del mapa (la capital).
- **Callao en POWER** no tiene celdas propias (`celdas: 0`): usa la celda de su capital, igual que Lima, con `nota`. Acéptalo, no lo corrijas.
- **Calcula con los años que haya y reporta `n_years`** (hoy 24 por serie; si el cron añade años, el cálculo no cambia).
- API actual: `/power/{region}`, `/gpm/{region}` (JSON tal cual) y `/api/zonas/{id}?variable=` (serie + `nota`). Falta `stats`.

## 2. Qué hay que calcular

Por **zona** (25) y por **variable** (lluvia, temperatura; decidir si también `T2M_MAX`/`T2M_MIN`), sobre la serie **anual** (método del Drive, v3 probada):

1. **Mann-Kendall con TFPW**: `pymannkendall.trend_free_pre_whitening_modification_test`. Alternativa: `hamed_rao_modification_test`. **No** Mann-Kendall estacional sobre meses (23–58 % de falsos positivos).
2. **Pendiente de Sen** sobre la serie anual: unidades por año → **×10 = por década**.
3. **Intervalo de la pendiente** con `scipy.stats.theilslopes(y, x, alpha=0.95)` (`pymannkendall` no lo da). También ×10.
4. **Benjamini-Hochberg** entre las 25 zonas de **la misma variable** (`statsmodels.stats.multitest.multipletests(method="fdr_bh")`) → `q_value`.
5. **`lag1`**: autocorrelación de un año al siguiente.
6. **`status`**: `real` si `q_value < 0.05`; `pocos_datos` si `n_years < 20` o `celdas < 4`; si no, `posible_casualidad` (ver sección 6).

Campos por zona (`stats`, contrato del `07`):

| Campo | Tipo | Nota |
|---|---|---|
| `slope_per_decade` | número | en la unidad de la variable por década |
| `intercept` | número | para dibujar la línea de Sen |
| `p_value`, `q_value` | número | antes y después de BH |
| `ci_low`, `ci_high` | número | de `theilslopes`, por década |
| `n_years` | entero | años con datos |
| `lag1` | número | |
| `status` | `"real"` · `"posible_casualidad"` · `"pocos_datos"` | siempre con texto en la ficha |

Propuestos en el `13` (**por confirmar**, hay que avisar a los 4): `year_start`, `year_end`, `pct_change_per_decade` (útil en lluvia), `source` y `period` por variable, y dos periodos (largo y reciente).

Guardar también `metadata.method` (método usado), unidad y fuente.

## 3. Cómo debe salir (propuesta, ajustable)

- **Reparto:** tú entregas el script y el JSON con los nombres de campo del `07`; quien mantiene la API (Leandro) añade `stats` al modelo Rust y a `/api/zonas/{id}`, regenera `openapi.json` y publica. Avisa cuando el JSON esté en `developer`.
- **Punto de partida:** `pipeline/exploracion/josue/scripts/lab5_tendencias.py` y `validar_lab5.py` ya hacen parte del cálculo; adáptalos a leer `data/*.json` en vez de la API.
- Script `pipeline/tendencias.py` que **lee** `data/power.json` y `data/gpm.json` y **escribe** JSON en `data/` (misma regla: precalculado, `allow_nan=False`).
- Forma sugerida alineada al Drive: lista de zonas por variable (sin series) y detalle por zona (serie + `stats`). Si se prefiere un solo `data/tendencias.json` por ahora, está bien: lo importante son los **nombres de campo del `07`**, porque la API Rust los va a deserializar tal cual.
- `id` de zona = **ubigeo como texto**: 01 Amazonas · 02 Áncash · 03 Apurímac · 04 Arequipa · 05 Ayacucho · 06 Cajamarca · 07 Callao · 08 Cusco · 09 Huancavelica · 10 Huánuco · 11 Ica · 12 Junín · 13 La Libertad · 14 Lambayeque · 15 Lima · 16 Loreto · 17 Madre de Dios · 18 Moquegua · 19 Pasco · 20 Piura · 21 Puno · 22 San Martín · 23 Tacna · 24 Tumbes · 25 Ucayali.

## 4. Reglas del repo que aplican

- Nunca `NaN`/`null`: una serie constante o muy corta puede dar `p`/`lag1` indefinidos; decidir un valor o `status: "pocos_datos"` y **no** escribir `NaN`.
- Si cambias la forma de un JSON, avisa al equipo (CONDITIONS.md) y actualiza `docs/`.
- Añade tu validación a `tests/e2e.sh` (`jq`) como se hizo con `power.json`/`gpm.json`.
- Dependencias nuevas a `pipeline/requirements.txt` (`scipy`, `pymannkendall`, `statsmodels`) **con versión fija** (`paquete==x.y.z`), como las demás.
- PR a `developer`, rama `feat/tendencias`, `changelog/feat-tendencias.md`, `bash tests/e2e.sh` en verde.

## 5. Trampas conocidas

- **Unidades:** Sen sobre serie anual da «por año»; ×10 para década. Sobre serie mensual cruda da «por mes» (olvidarlo cambió +10 mm/década en +7,5 en las pruebas).
- **Costa:** el píxel de la capital no es fiable (Piura 2017 = 2,60 con IMERG frente a 0,33 con CHIRPS; IMERG sobreestima en el desierto costero). Decidido: promedio del departamento (hay un cálculo de partida en `pipeline/exploracion/`).
- **El Niño:** con 25 años y persistencia fuerte ningún método baja del todo al 5 % de falsos positivos; por eso el semáforo dice «posible casualidad» y no «no hay cambio».
- **El periodo cambia el signo** de la lluvia en Apurímac, Loreto y Piura (hallazgo de Favio): la ficha debe mostrar siempre desde qué año se calcula.

## 6. Decisiones

**Decididas (2026-11-14):**
- Unidad geográfica = **promedio del departamento** (todas las regiones). Hecho en la #22 (`pipeline/departamentos.py`).
- Temperatura de la primera versión = `T2M`.
- **Periodo = 2001–2024 para las dos variables** (POWER y GPM). Si hace falta un periodo largo (1981) o lluvia de largo plazo (GPCP), es otra decisión y otra columna de salida.

- **Semáforo (umbrales de Josue, Sebastian 14 nov):** `pocos_datos` si `n_years < 20` o `celdas < 4`; `real` si `q_value < 0.05`; si no, `posible_casualidad`. `pct_change_per_decade` solo en lluvia.
- **`aviso`** (texto): en todas las zonas de lluvia, por el cambio de constelación de IMERG en 2014 (TRMM → GPM: la tendencia puede estar sesgada a la baja); y en cualquier zona si `lag1 > 0.5`. Si hay los dos, van en el mismo texto.
- **Archivos:** uno por ruta: `data/variables.json`, `data/zonas/{variable}.json` (sin serie) y `data/zonas/{variable}/{id}.json` (serie + `stats`), generados por `pipeline/tendencias.py`.

**Pendientes:**
1. ¿También `T2M_MAX`/`T2M_MIN`? La primera versión solo `T2M`.
