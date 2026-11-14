# Resultados reales de la colección de Bruno

**Ejecutado:** 14 nov 2026, con `correr_bruno.py` sobre los `.yml` de `~/bruno/Detective Josue` (environment `Peru`, 1981–2024).
**JSON completo:** `resultados/bruno_resultados.json`

| Petición | HTTP | Tiempo (s) | Tamaño (KB) | Estado |
|---|---|---|---|---|
| 1 POWER (Lab 1)/1 Piura | 200 | 0,94 | 58,1 | ok |
| 1 POWER (Lab 1)/2 Tumbes | 200 | 0,91 | 58,1 | ok |
| 1 POWER (Lab 1)/3 Puno | 200 | 1,19 | 56,8 | ok |
| 1 POWER (Lab 1)/4 Lima | 200 | 1,14 | 57,8 | ok |
| 1 POWER (Lab 1)/5 Iquitos | 200 | 1,17 | 58,2 | ok |
| 1 POWER (Lab 1)/6 Recuadro Peru NO | 200 | 1,77 | 2.243,4 | ok |
| 1 POWER (Lab 1)/7 Recuadro Peru NE | 200 | 1,49 | 1.122,8 | ok |
| 1 POWER (Lab 1)/8 Recuadro Peru SO | 200 | 1,77 | 2.348,6 | ok |
| 1 POWER (Lab 1)/9 Recuadro Peru SE | 200 | 1,68 | 1.157,1 | ok |
| 3 AppEEARS (Lab 3)/1 Login AppEEARS | — | — | — | saltada (credencial) |
| 3 AppEEARS (Lab 3)/2 Capas MOD13A3 | 200 | 0,47 | 5,9 | ok |
| 3 AppEEARS (Lab 3)/3 Mis tareas | — | — | — | saltada (credencial) |

## Lo que devolvió cada grupo

**POWER, puntos (1–5):** 7 variables (`GWETTOP, PRECTOTCORR, QV2M, RH2M, T2M, T2M_MAX, T2M_MIN`), 528 meses y **0 valores `-999`** en los 5 puntos. Unidades: °C, mm/day, g/kg, %, 1.

**POWER, recuadros (6–9):** 266 + 133 + 280 + 140 = **819 celdas**, sin mensajes de error. Una variable de 44 años pesa entre 1,1 y 2,3 MB por recuadro; **las 4 variables de todo Perú suman unos 27 MB**. Es un dato útil para el contrato y para Sebastian.

**AppEEARS, capas MOD13A3:** existen `_1_km_monthly_NDVI` y `_1_km_monthly_EVI` (escala 0,0001, relleno -3000, rango válido -0,2 a 1), `_1_km_monthly_pixel_reliability` (0–3, relleno -1), `_1_km_monthly_VI_Quality` y las reflectancias. **Confirma el nombre de capa de la guía 12** (`_1_km_monthly_NDVI`).

**Login de AppEEARS (comprobado aparte con la credencial de `~/.netrc`):** falla. El servidor de Earthdata responde `invalid_credentials`.
