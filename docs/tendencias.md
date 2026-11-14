# Cálculo de tendencias (responsable: Sebastian)

> **Cambio del 14 nov 2026:** el cálculo de tendencias pasa de Josue a **Sebastian**. Josue sigue con los datos (descarga y promedio por departamento).

Qué hay hecho, qué falta calcular y cómo debe quedar. Fuente de las decisiones: Drive (`07-stack-decidido`, `13-datos-unificado-14nov`, `06-datos-a-usar`) y [`reglas-datos.md`](reglas-datos.md). **Los campos de tendencia están en progreso: lo marcado «por confirmar» lo decide Sebastian con el equipo.**

## 1. Qué tenemos (entrada)

Dos JSON en `data/`, generados por `pipeline/` (la API nunca calcula en vivo). Misma forma:

```json
[{"region": "Lima", "lat": -12.05, "lon": -77.04,
  "anios": {"2017": {"PRECTOTCORR": 0.155, "T2M": 18.5375, "T2M_MAX": 24.3633, "T2M_MIN": 14.0408}}}]
```

| Variable del producto | Archivo | Campo | Unidad | Fuente | Periodo |
|---|---|---|---|---|---|
| **Lluvia** | `data/gpm.json` | `lluvia_mm_dia` | mm/día | GPM IMERG v07 (NASA, ~10 km) | **2001–2024** (IMERG empieza en jun 2000 y el 2025 no está completo; el pipeline descarta años incompletos) |
| **Temperatura** | `data/power.json` | `T2M` (+ `T2M_MAX`, `T2M_MIN`) | °C | MERRA-2 vía POWER (~50 km) | desde 2000 (POWER llega a 1981) |
| Lluvia POWER | `data/power.json` | `PRECTOTCORR` | mm/día | POWER | solo referencia, **no** va a la ficha |

- Ya vienen **promediados por año** y solo con **años completos (12 meses)**. Nunca `NaN`.
- **Hoy** 25 regiones = 25 capitales (un píxel por región). **Decidido (2026-11-14): la unidad final es el promedio del departamento**, para todas las regiones; falta implementarlo en el pipeline y las tendencias deben calcularse sobre ese promedio (ver sección 6). Lima y Callao comparten celda POWER (idénticos): decisión aceptada.
- `developer` hoy tiene 2015–2020; la ampliación a 2000+ va en la rama `feat/datos-desde-2000`. **Calcular con los años que haya y reportar `n_years`.**
- API actual: `/power/{region}`, `/gpm/{region}`. Hasta que el contrato nuevo exista, sirve los promedios anuales.

## 2. Qué hay que calcular

Por **zona** (25) y por **variable** (lluvia, temperatura; decidir si también `T2M_MAX`/`T2M_MIN`), sobre la serie **anual** (método del Drive, v3 probada):

1. **Mann-Kendall con TFPW**: `pymannkendall.trend_free_pre_whitening_modification_test`. Alternativa: `hamed_rao_modification_test`. **No** Mann-Kendall estacional sobre meses (23–58 % de falsos positivos).
2. **Pendiente de Sen** sobre la serie anual: unidades por año → **×10 = por década**.
3. **Intervalo de la pendiente** con `scipy.stats.theilslopes(y, x, alpha=0.95)` (`pymannkendall` no lo da). También ×10.
4. **Benjamini-Hochberg** entre las 25 zonas de **la misma variable** (`statsmodels.stats.multitest.multipletests(method="fdr_bh")`) → `q_value`.
5. **`lag1`**: autocorrelación de un año al siguiente.
6. **`status`**: `real` si `q_value < 0.05`; `pocos_datos` si `n_years < 10`; si no, `posible_casualidad` (umbrales **por confirmar por Sebastian**).

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

- Script `pipeline/tendencias.py` que **lee** `data/power.json` y `data/gpm.json` y **escribe** JSON en `data/` (misma regla: precalculado, `allow_nan=False`).
- Forma sugerida alineada al Drive: lista de zonas por variable (sin series) y detalle por zona (serie + `stats`). Si se prefiere un solo `data/tendencias.json` por ahora, está bien: lo importante son los **nombres de campo del `07`**, porque la API Rust los va a deserializar tal cual.
- `id` de zona = **ubigeo como texto**: 01 Amazonas · 02 Áncash · 03 Apurímac · 04 Arequipa · 05 Ayacucho · 06 Cajamarca · 07 Callao · 08 Cusco · 09 Huancavelica · 10 Huánuco · 11 Ica · 12 Junín · 13 La Libertad · 14 Lambayeque · 15 Lima · 16 Loreto · 17 Madre de Dios · 18 Moquegua · 19 Pasco · 20 Piura · 21 Puno · 22 San Martín · 23 Tacna · 24 Tumbes · 25 Ucayali.

## 4. Reglas del repo que aplican

- Nunca `NaN`/`null`: una serie constante o muy corta puede dar `p`/`lag1` indefinidos; decidir un valor o `status: "pocos_datos"` y **no** escribir `NaN`.
- Si cambias la forma de un JSON, avisa al equipo (CONDITIONS.md) y actualiza `docs/`.
- Añade tu validación a `tests/e2e.sh` (`jq`) como se hizo con `power.json`/`gpm.json`.
- Dependencias nuevas a `pipeline/requirements.txt` (`scipy`, `pymannkendall`, `statsmodels`).
- PR a `developer`, rama `feat/tendencias`, `changelog/feat-tendencias.md`, `bash tests/e2e.sh` en verde.

## 5. Trampas conocidas

- **Unidades:** Sen sobre serie anual da «por año»; ×10 para década. Sobre serie mensual cruda da «por mes» (olvidarlo cambió +10 mm/década en +7,5 en las pruebas).
- **Costa:** el píxel de la capital no es fiable (Piura 2017 = 2,60 con IMERG frente a 0,33 con CHIRPS; IMERG sobreestima en el desierto costero). Decidido: promedio del departamento (hay un cálculo de partida en `pipeline/exploracion/`).
- **El Niño:** con 25 años y persistencia fuerte ningún método baja del todo al 5 % de falsos positivos; por eso el semáforo dice «posible casualidad» y no «no hay cambio».
- **El periodo cambia el signo** de la lluvia en Apurímac, Loreto y Piura (hallazgo de Favio): la ficha debe mostrar siempre desde qué año se calcula.

## 6. Decisiones

**Decididas (2026-11-14):**
- Unidad geográfica = **promedio del departamento** (todas las regiones). Parte de Josue (datos): adaptar el cálculo de `pipeline/exploracion/` (GeoJSON de departamentos + `regionmask`) para que `power.json` y `gpm.json` salgan por departamento, con la misma forma. Después Sebastian calcula las tendencias sobre ese promedio.
- Temperatura de la primera versión = `T2M`.

**Pendientes:**
1. Periodos: ¿temperatura 1981–2024 (largo) y 2001–2024 (reciente)? ¿Lluvia solo 2001–2024 o también largo plazo (GPCP)?
2. Umbrales exactos del semáforo y `pct_change_per_decade`.
3. Forma final de los archivos (por variable/por zona) y de las rutas `/api/...`.
