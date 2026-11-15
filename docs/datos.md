# NASA POWER: conceptos rápidos

## Qué es
**POWER** (Prediction Of Worldwide Energy Resources) es una API de NASA con datos meteorológicos y solares de todo el mundo. Mezcla satélites y modelos de reanálisis (MERRA-2) y los entrega en una malla de ~0.5° × 0.625° (unos 50 × 60 km). No son estaciones: cada punto es el promedio de su celda.

## Variables usadas

| Código | Qué mide | Unidad | Nota |
|---|---|---|---|
| `PRECTOTCORR` | Precipitación total, corregida por sesgo | mm/día | El valor es el promedio diario del mes. Para el total mensual, multiplicar por los días del mes. |
| `T2M` | Temperatura del aire a 2 m del suelo | °C | Promedio mensual. Es la temperatura "de clima", no la de la superficie. |
| `T2M_MAX` | Temperatura máxima a 2 m | °C | Promedio de las máximas diarias del mes. |
| `T2M_MIN` | Temperatura mínima a 2 m | °C | Promedio de las mínimas diarias del mes. |

**Fuente de temperatura (decisión del equipo, 2026-11-14):** MERRA-2, a través de POWER. POWER ya usa MERRA-2 por debajo, así que no se baja MERRA-2 aparte (cada archivo pesa ~75 MB).

- **Corregida (`CORR`)**: se ajusta el modelo con observaciones (GPCP) para reducir el error. Por eso se prefiere a `PRECTOT`.
- **Resumen por región (primera versión, 2015-2020; ahora el JSON cubre 2001–2024)**: Loreto y Madre de Dios son las más lluviosas (6-8 mm/día). La costa (Tacna, Lima, Callao) casi no llueve (~0.1). La temperatura baja con la altura: Huancavelica y Pasco ~5-7 °C, y la selva ~25-27 °C.

## Parámetros de la consulta

| Parámetro | Valor | Significado |
|---|---|---|
| `temporal` | `monthly/regional` | Datos mensuales de un recuadro (máx. 10° por lado). `power.py` pide 4 recuadros que cubren Perú y promedia las celdas de cada departamento. |
| `community` | `AG` | Comunidad agroclimática: define unidades y nombres de variables. |
| `latitude-min/max`, `longitude-min/max` | los 4 recuadros de Perú | Límites de cada consulta. `lat`/`lon` de cada región en el JSON siguen siendo su capital, solo como punto del mapa. |
| `start`, `end` | años | Rango pedido. En mensual se piden como `YYYY`. |
| `format` | `JSON` | Formato de respuesta. |

## Estructura de la respuesta
`datos["properties"]["parameter"]` contiene un diccionario por variable, con claves `YYYYMM`:

```
{"PRECTOTCORR": {"201701": 1.2, ..., "201713": 0.9}, "T2M": {...}, "T2M_MAX": {...}, "T2M_MIN": {...}}
```

## Limpieza (lo que hace el script)
1. **Claves que terminan en `13`**: es el promedio anual que POWER añade (mes "13"). Se quitan para no duplicar información.
2. **`-999`**: valor de "sin dato". Se cambia por `NaN` y el mes se descarta.
3. **`groupby(año).mean()`**: promedio de los 12 meses de cada año. Solo se guardan los **años completos**: un año con algún mes sin dato (o el año en curso) no aparece en el JSON. Así `data/power.json` nunca contiene `NaN`, que no es JSON válido y haría caer la API al arrancar.

## Limitaciones
- **Resolución gruesa**: Lima y Callao caen en la misma celda y dan valores idénticos. Decisión del equipo: se deja así.
- **Promedio del departamento** (no el píxel de la capital): todas las celdas cuyo centro cae dentro del departamento. Los departamentos con menos de 4 celdas (Callao, Tumbes, Lambayeque) llevan `nota`; Callao no tiene celdas propias y usa la de su capital.
- **Es un modelo**: puede errar en zonas de montaña o con lluvias muy locales.

## Hallazgo útil: Niño Costero 2017
En 2017 la lluvia subió mucho en la costa norte: Piura pasó de 0.28 a 1.84 mm/día, Lambayeque de 0.32 a 0.94 y Tumbes de 1.34 a 2.84. Es la misma señal que se busca con GPM IMERG en marzo de 2017.

Reglas generales (años completos, costa, fuentes): [`reglas-datos.md`](reglas-datos.md).

## Archivos
- `pipeline/power.py`: consulta las 25 regiones y escribe `data/power.json` (tabla región × año con `PRECTOTCORR`, `T2M`, `T2M_MAX` y `T2M_MIN`).

## Malla de temperatura (mapa de calor)

`pipeline/power.py` también escribe `data/celdas/temperatura.json`: la `T2M` anual de **cada celda**
de POWER cuyo centro cae en un departamento (344 celdas, 2001–2024). La sirve `GET /api/celdas?variable=temperatura`
y el frontend la pinta como mapa de calor (1 px por celda, interpolación bilineal, recortada por los polígonos).

**Por qué celdas y no el promedio del departamento:** el promedio mezcla costa, Andes y selva. Lima sale
13,8 °C y Pasco 19,6 °C, cifras que nadie reconoce. La celda muestra el valor donde está: costa de Lima ~18 °C,
altiplano de Puno ~8 °C, Iquitos ~26 °C. Las tendencias por departamento (°C/década) sí usan el promedio:
para el cambio no importa mezclar alturas.

**Límites conocidos:**
- La celda (~50 km) tiene la elevación media de MERRA-2: en los Andes los valles salen más fríos y las cumbres
  más templadas que una estación (Cusco ciudad ~12 °C, su celda ~8 °C). La leyenda lo dice.
  Fuente: respuesta del equipo POWER en el [foro de Earthdata](https://forum.earthdata.nasa.gov/viewtopic.php?p=16275).
- Las tendencias 2001–2024 (0,14–0,77 °C/década) son coherentes con estudios andinos (0,13–0,45 °C/década,
  p. ej. [SENAMHI, 1964–2014](https://www.sidalc.net/search/Record/dig-senamhi-pe-20.500.12542-142)).
  Ucayali (0,77) es el más alto de todos: revisado abajo, en «Ucayali: la tendencia más alta».
- Mejora futura: [PISCOt v1.2](https://link.springer.com/article/10.1038/s41597-023-02777-w) de SENAMHI
  (~1 km, corrige por topografía, MAE ~1,3 °C), pero solo llega a 2020.

### Ucayali: la tendencia más alta (revisado 2026-11-15)

Ucayali sube **0,77 °C/década** (2001–2024, Theil-Sen sobre `power.json`), el máximo de los 25 departamentos y
`real` con el criterio único. Qué muestran los datos del repo:

| °C/década | 2001–2024 | 2001–2022 | 2001–2019 |
|---|---|---|---|
| **Ucayali** | **0,77** | **0,58** | **0,45** |
| Huánuco | 0,55 | 0,36 | 0,16 |
| Pasco | 0,46 | 0,26 | 0,06 |
| Loreto | 0,26 | 0,13 | 0,02 |
| San Martín | 0,25 | 0,08 | −0,11 |
| Madre de Dios | 0,14 | 0,05 | −0,01 |

- **No es una celda mala:** de las 31 celdas de Ucayali, 27 suben más de 0,5 °C/década (entre 0,34 y 1,18; mediana 0,84).
- **Pesa mucho el final de la serie:** de 2001 a 2022 el promedio anual está entre 25,0 y 26,7 °C; en 2023 y 2024 sale
  28,2 y 28,5 °C. Quitar esos dos años baja la pendiente a 0,58. Sigue siendo la más alta de la selva baja
  (Loreto 0,13, Madre de Dios 0,05 en el mismo periodo), y con el periodo 2001–2019 todavía da 0,45.
- **Hay coherencia espacial:** Huánuco y Pasco, vecinos de Ucayali en la selva central, también están entre los más altos.
  Un artefacto de una sola región sería menos probable que un patrón que cruza tres departamentos.
- **Lo que no se puede decir con estos datos:** si la causa es calentamiento real (incluida la deforestación de
  Ucayali), el calor extremo de 2023–2024, o un cambio en las observaciones que alimentan el reanálisis MERRA-2.
  Distinguirlo exige una fuente independiente (estaciones de SENAMHI, ERA5-Land o temperatura de superficie de MODIS).
- **La comparación con «estudios andinos» (0,13–0,45) no es del todo justa:** Ucayali es selva baja y esos estudios
  miden estaciones andinas hasta 2014.

**Decisión:** la tendencia se publica tal cual (`real`, sin cambiar el umbral), pero Ucayali lleva un aviso propio en
`stats.aviso` (`avisos_zona` de `temperatura` en `pipeline/tendencias.py`, por ubigeo): dice que la subida depende de los
dos últimos años, cuánto baja sin ellos (0,77 → 0,58) y que estos datos no separan calentamiento real, calor extremo y un
cambio del reanálisis. Los números salen de la serie, así que el texto se actualiza solo al regenerar. Va delante del aviso
de lag1 si algún día aplica. Los demás departamentos no cambian.

## Malla de lluvia

`pipeline/power.py` escribe también `data/celdas/lluvia.json`: la `PRECTOTCORR` de cada celda de POWER (las mismas
344 celdas que la temperatura), como **media diaria del año × 365 = mm/año**, en enteros, con el campo `valor`
(la temperatura conserva `t2m` para no romper el contrato). La sirve `GET /api/celdas?variable=lluvia`. Coincide
celda por celda con la copia del frontend (`nasa-challenge-frontend/src/data/celdas_lluvia.json`): 0 diferencias.

**La unidad la manda cada respuesta.** `/api/variables` y `/api/zonas` dan la lluvia en **mm/día** (promedio diario,
como POWER e IMERG); `/api/celdas?variable=lluvia` la da en **mm/año**, que se lee mejor en un mapa. No se unificó para
no romper el contrato de las tendencias. Cada respuesta de `/api/celdas` trae su campo `unidad`: el frontend lee la
unidad de la malla de ahí, nunca de `/api/variables`.

Solo las mallas, sin tocar `power.json` (8 llamadas a POWER): `python pipeline/power.py celdas`.

## Malla de vegetación

`pipeline/vegetacion_malla.py` escribe `data/celdas/vegetacion.json` (NDVI anual por celda, `GET /api/celdas?variable=vegetacion`)
y `data/ndvi_departamentos.json` (NDVI anual por departamento, fuente de `zonas/vegetacion.json`, que escribe
`pipeline/tendencias.py`).

- **Fuente:** MODIS MOD13A3 v061 (NASA LP DAAC), NDVI mensual a 1 km, pedido a AppEEARS (el mismo producto del Caso 2,
  `pipeline/ndvi.py`). Se pide en 4 solicitudes de 6 años sobre el recuadro del Perú (−81,5, −18,5, −68,5, 0,1).
- **Método, por píxel de 1 km:** un mes vale si `pixel_reliability` es 0 o 1 (quita nubes, nieve y agua, como `ndvi.py`);
  el NDVI del año es la media de sus meses válidos si tiene **al menos 6**. La celda de 0,25° (~27 km) es la media de sus
  píxeles con año válido, si son al menos la mitad de los que alguna vez tienen dato (el mar no cuenta); si no, `null`.
- **Por qué 6 meses y no 12:** en la selva y los Andes casi siempre hay nubes en algún mes; con 12 de 12 por píxel la selva
  quedaría vacía. Va escrito en la `nota` del archivo.
- **Departamento:** media de sus celdas (centro dentro del polígono, como `celdas_json()` de `power.py`), solo los años en
  que al menos la mitad de sus celdas tiene dato. Sin celdas propias se usa la más cercana a la capital, con `nota`.
- **Límite conocido:** en la selva el NDVI se satura (~0,8–0,9): muestra dónde hay vegetación, no cuánto bosque se pierde
  (para eso, `/api/cobertura-arboles`). `zonas/vegetacion.json` lleva un `aviso` cuando el NDVI medio del departamento es
  0,75 o más (`aviso_saturado` en `tendencias.py`).
- **Validación al arrancar** (`Datos::validar_celdas`): no vacía, dentro de Perú, años dentro de `variables.json`,
  unidad `NDVI`, solo el campo `valor`, valores en −0,2..1 y ninguna celda con todo `null`. Los límites van por variable:
  −40..50 °C (temperatura), 0..12 000 mm/año (lluvia).
- **Refresco:** a mano, una vez al año: `enviar` → `estado` → `bajar` → `calcular` y luego `python pipeline/tendencias.py`.
  Si falta algún bloque, `calcular` lo avisa y la malla llega hasta el último año leído (nunca se inventan años).
- **Serie corta = `pocos_datos` con `nota`:** con menos de 20 años no se mide tendencia; cada departamento lleva una
  `nota` con los años que tiene («Serie de solo 12 años (2001–2012)…»), para no confundirlo con «pocas celdas».
  `tests/e2e.sh` exige que `variables.json` y `zonas/vegetacion.json` acaben en el mismo año que la malla.
