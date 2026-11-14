# Reglas de datos (decisiones del equipo)

Valen para todo `pipeline/*.py` y todo `data/*.json`, hoy y en los que se añadan (POWER, GPM, CHIRPS, MERRA-2, NDVI…). Decididas el 2026-11-14.

## 1. Solo años completos (12 meses)
- Un año entra al JSON **solo si tiene los 12 meses con dato**. Nunca el año en curso ni uno con meses vacíos.
- **Por qué**: un promedio de ene–oct no se puede comparar con años enteros (la estación del año lo sesga), y si el pipeline pide meses que aún no existen (CHIRPS, GPM) falla y el cron no guarda nada.
- **Cómo**: contar meses con dato por año y descartar los que no sean 12. Ejemplo en `pipeline/power.py` (`g.size() == 12`).
- Efecto: el último año del JSON es el año anterior. El año nuevo entra en enero siguiente.

## 2. Nunca `NaN` ni `null` en los JSON
- `json.dumps(..., allow_nan=False)` siempre. Un `NaN` hace caer la API al arrancar.
- Un punto sin dato (p. ej. mar en CHIRPS) se trata como `NaN` *dentro* del script; si deja un año incompleto, ese año se descarta (regla 1).
- El CI valida cada `data/*.json` con `jq` en `tests/e2e.sh`.

## 3. Una fuente = un JSON = un número
- Cada fuente tiene su archivo (`power.json`, `gpm.json`, `chirps.json`…) con la **unidad en el nombre de la variable** (`lluvia_mm_dia`).
- **No se mezclan ni se promedian fuentes** en un solo valor: si discrepan, se muestran por separado con su nombre.

## 3b. Fuentes elegidas (decididas el 2026-11-14)
| Variable | Fuente del producto | Archivo | Notas |
|---|---|---|---|
| **Lluvia** | **GPM IMERG** (NASA, `GPM_3IMERGM` v07, ~10 km) | `data/gpm.json` | Es la única lluvia que muestra la ficha. Periodo reciente 2001–2024 (IMERG empieza en jun 2000). |
| **Temperatura** | **MERRA-2 vía POWER** (`T2M`, `T2M_MAX`, `T2M_MIN`) | `data/power.json` | POWER ya usa MERRA-2: no se baja MERRA-2 aparte. |

- **Unidad geográfica: promedio del departamento** (todas las regiones, no solo la costa), no el píxel de la capital. Los JSON de hoy siguen siendo del píxel de la capital hasta que el pipeline lo implemente (parte de Josue; hay un cálculo de partida en `pipeline/exploracion/`).
- **Temperatura en la primera versión: solo `T2M`.** `T2M_MAX` y `T2M_MIN` quedan en `power.json` como extra si sobra tiempo; la API no las expone todavía.
- **CHIRPS descartado**: no es de NASA y daría una segunda lluvia que contradice a IMERG en la costa (regla 3). La rama `feat/pipeline-chirps` queda en GitHub por si se retoma; no entra a `developer`.
- **`PRECTOTCORR` de POWER** sigue en `power.json` solo como referencia: la ficha no la muestra.
- Si hace falta lluvia de largo plazo (desde 1981/1983), es una decisión aparte (propuesta del Drive: GPCP v3.2).

## 4. Puntos poco fiables (la costa y casos parecidos)
Un solo píxel de la capital no representa la región cuando las fuentes discrepan. Caso real (comparación hecha antes de descartar CHIRPS): Piura 2017 = 2,60 (GPM) vs 0,33 (CHIRPS); en el desierto costero GPM sobreestima (~100 mm/año de más).

Al detectar un caso así:
1. **Usar el promedio del departamento** en vez del píxel de la capital: ya es la regla para todas las regiones (sección 3b). Mientras el pipeline no lo implemente, estas regiones llevan la `nota` (ver `pipeline/exploracion/lab4_departamentos.py` y `pipeline/exploracion/josue/`).
2. **Mostrar siempre fuente y unidad** en la respuesta de la API.
3. **Añadir un campo `nota`** en las regiones afectadas (p. ej. "IMERG sobreestima la lluvia en el desierto costero").
4. **Documentar el caso** aquí o en `docs/datos.md` (qué región, qué fuentes, cuánto difieren).
- Lima y Callao (misma celda POWER, datos idénticos) se dejan tal cual: decisión del equipo.

## 5. Cómo añadir una regla
Una PR a `developer` que edite este archivo y lo enlace desde el changelog. Cambiar una regla = avisar al equipo.
