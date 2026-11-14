# Scripts

Se corren desde `pipeline/exploracion/josue/`. Leen de `data/` y escriben en `salida/` (las dos carpetas están en `.gitignore`; la foto de los resultados del 14 nov está en `resultados/`). **Ninguno contiene credenciales.**

| Orden | Script | Necesita | Qué hace | Salida | Probado |
|---|---|---|---|---|---|
| 1 | `lab1_power.py` | Solo biblioteca estándar | POWER mensual 1981–2024 en 5 puntos, 7 variables; faltantes, unidades, picos de lluvia | `lab1_power_{mensual,anual}.csv`, `lab1_power_resumen.json` | ✅ |
| 2 | `lab4_celdas_departamento.py` | Solo biblioteca estándar + GeoJSON | Celdas de IMERG, GPCP y POWER por departamento (ray casting, con huecos y MultiPolygon); autoprueba | `lab4_celdas_departamento.csv` | ✅ (igual que `regionmask`) |
| 3 | `lab5_tendencias.py` | Solo biblioteca estándar | TFPW + Sen + IC 95 % + BH; autoprueba con series sintéticas; aplicado a los 5 puntos | `lab5_tendencias.{csv,json}` | ✅ |
| 4 | `power_departamentos.py` | `.venv` | Malla POWER en 4 recuadros → `regionmask` → promedio por departamento → tendencias con umbral exigente | `power_departamentos_{anual,tendencias}.csv`, `.json` | ✅ |
| 5 | `validar_lab5.py` | `.venv` | Compara el paso 3 con `pymannkendall`, `scipy` y `statsmodels` en 192 series | `validacion_lab5.json` | ✅ |
| 6 | `correr_bruno.py` | `.venv` | Ejecuta las peticiones de la colección de Bruno (YAML) y resume cada respuesta | `bruno_resultados.{json,md}` | ✅ |
| 7 | `graficos.py` | `.venv` | PNG del Caso 1 y de las tendencias por departamento | `*.png` | ✅ |
| 8 | `lab2_imerg_gpcp.py` | `.venv` + credencial Earthdata | Lab 0 (login) + Lab 2: baja marzo de 2017 de IMERG y GPCP, recorta a Perú y reporta unidades y NaN | `lab2_*_peru_201703.nc` | ⛔ Bloqueado (credencial inválida) |

## Decisiones de diseño

- **Labs 1, 4 y 5 sin dependencias**, para que cualquiera del equipo los corra sin instalar nada. El pipeline final usará las librerías (ya validadas como equivalentes).
- **Caché:** `power_departamentos.py` guarda las respuestas regionales en `data/power_regional/`; volver a correrlo no consulta la API.
- **`power_departamentos.py` importa el método de `lab5_tendencias.py`:** una sola implementación, la validada.
- **Umbral en constantes al inicio del script** (`MIN_CELDAS = 4`, `MIN_AÑOS = 20`, `MAX_LAG1 = 0.5`, `ALFA = 0.05`), fácil de cambiar si el equipo decide otro.
