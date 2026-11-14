# Lab 5 — Método de tendencia y su validación

**Scripts:** `lab5_tendencias.py` (método + autoprueba) y `validar_lab5.py` (comparación con las librerías)

## Método (06-datos-a-usar.md, sección 3)

1. Media anual (solo años con 12 meses).
2. **Mann-Kendall con pre-whitening sin tendencia** (TFPW, Yue et al. 2002).
3. **Pendiente de Sen** por década con IC 95 %.
4. **Benjamini-Hochberg** entre zonas → `q_value`.
5. **Umbral exigente** (decisión de Josue, 14 nov):

| Estado | Condición |
|---|---|
| `pocos_datos` | menos de 4 celdas **o** menos de 20 años |
| `real` | q < 0,05 **y** el IC 95 % de Sen no incluye 0 **y** \|lag1\| ≤ 0,5 |
| `posible_casualidad` | el resto. El motivo se guarda en el campo `motivo` |

La condición de `lag1` sale del Lab 1: la lluvia de Iquitos daba q < 0,001 con `lag1` = 0,74, por un salto de los datos y no por una tendencia.

## Validación contra las librerías del stack

`validar_lab5.py` compara las **192 series** departamentales de POWER (4 variables × 24 departamentos × 2 periodos):

| Comparación | Diferencia máxima |
|---|---|
| p-valor TFPW frente a `pymannkendall.trend_free_pre_whitening_modification_test` | 2,2e-16 |
| Pendiente de Sen frente a `scipy.stats.theilslopes` | 0 |
| IC 95 % frente a `scipy.stats.theilslopes` | 0,0008 por año (0,008 por década) |
| q de BH frente a `statsmodels multipletests(fdr_bh)` | 2,2e-16 |

**Conclusión:** el método es correcto. La pequeña diferencia del IC viene del redondeo de rangos de scipy. **En el pipeline conviene usar directamente `pymannkendall`, `scipy` y `statsmodels`**, como dice el stack.

## Prueba en los 5 puntos (`salida/lab5_tendencias.csv`)

- `T2M` 1981–2024: +0,09 a +0,26 °C por década. Con BH entre 5 puntos, 4 salen significativos (todos menos Piura).
- `T2M` 2001–2024: ninguno pasa BH (q entre 0,050 y 0,063). Menos años y la corrección quitan potencia.
- **Lluvia de Lima 2001–2024:** q = 0,006 pero solo +0,03 mm/día por década. Significativo, pero irrelevante.
- **Lluvia de Iquitos 1981–2024:** +0,88 mm/día por década con q < 0,001 y `lag1` = 0,74. Es el artefacto. Con el umbral exigente ya no sale `real`.

## Lecciones para la ficha

1. Mostrar siempre `year_start`–`year_end`: el signo cambia con el periodo (Iquitos pasa de +0,88 a −0,96).
2. Mostrar `pct_change_per_decade` en lluvia; los mm/día sueltos engañan.
3. El mismo umbral para 44 y 24 años, sin rebajarlo para series cortas.
