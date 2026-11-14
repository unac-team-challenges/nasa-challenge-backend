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
| `temporal` | `monthly/point` | Datos mensuales de un solo punto (lat/lon). |
| `community` | `AG` | Comunidad agroclimática: define unidades y nombres de variables. |
| `latitude`, `longitude` | capital de cada región | Punto de consulta. |
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
- **Una capital por región**: no representa toda la región. Cusco capital no equivale a su selva, y Loreto en Iquitos no equivale a sus Andes.
- **Es un modelo**: puede errar en zonas de montaña o con lluvias muy locales.

## Hallazgo útil: Niño Costero 2017
En 2017 la lluvia subió mucho en la costa norte: Piura pasó de 0.28 a 1.84 mm/día, Lambayeque de 0.32 a 0.94 y Tumbes de 1.34 a 2.84. Es la misma señal que se busca con GPM IMERG en marzo de 2017.

Reglas generales (años completos, costa, fuentes): [`reglas-datos.md`](reglas-datos.md).

## Archivos
- `pipeline/power.py`: consulta las 25 regiones y escribe `data/power.json` (tabla región × año con `PRECTOTCORR`, `T2M`, `T2M_MAX` y `T2M_MIN`).
