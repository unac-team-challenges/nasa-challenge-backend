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
  Ucayali (0,77) es atípico: pendiente revisar si es deforestación real o un artefacto del reanálisis.
- Mejora futura: [PISCOt v1.2](https://link.springer.com/article/10.1038/s41597-023-02777-w) de SENAMHI
  (~1 km, corrige por topografía, MAE ~1,3 °C), pero solo llega a 2020.
