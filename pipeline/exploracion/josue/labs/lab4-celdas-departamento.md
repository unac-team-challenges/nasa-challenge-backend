# Lab 4 — GeoJSON de departamentos y celdas por zona

**Script:** `lab4_celdas_departamento.py` (biblioteca estándar, con autoprueba)
**GeoJSON:** `juaneladio/peru-geojson` → `peru_departamental_simple.geojson` (140 KB, 25 departamentos)

## El GeoJSON

| Campo | Contenido | Tipo |
|---|---|---|
| `FIRST_IDDP` | Ubigeo `"01"`–`"25"` | **Texto con cero inicial** ✅ (coincide con el contrato) |
| `NOMBDEP` | Nombre en mayúsculas | Texto |
| `HECTARES` | Área | Número |

25 departamentos (Lima es uno solo). Geometrías `Polygon` y `MultiPolygon`. No hace falta simplificarlo.

## Método y validación

Se cuentan los centros de celda dentro de cada polígono, el mismo criterio de `regionmask`. **Validado: `regionmask.mask_geopandas` da exactamente los mismos conteos en las 3 mallas** (0 diferencias en 75 comparaciones).

| Dataset | Celda | Centros |
|---|---|---|
| IMERG | 0,1° | x.x5 |
| GPCP | 0,5° | x.25 / x.75 |
| POWER | 0,5° × 0,625° | lat x.0 / x.5; lon = -180 + k·0,625 (comprobado con la API) |

## Celdas por departamento (ordenado de menos a más)

| Ubigeo | Departamento | km² | IMERG | GPCP | POWER |
|---|---|---|---|---|---|
| 07 | CALLAO | 141 | **1** | **0** | **0** |
| 24 | TUMBES | 4.690 | 37 | **2** | **1** |
| 14 | LAMBAYEQUE | 14.342 | 118 | 5 | **3** |
| 18 | MOQUEGUA | 15.807 | 131 | 6 | 5 |
| 23 | TACNA | 16.083 | 138 | 4 | 4 |
| 11 | ICA | 21.081 | 175 | 6 | 6 |
| 03 | APURIMAC | 21.114 | 176 | 7 | 6 |
| 09 | HUANCAVELICA | 22.065 | 186 | 6 | 5 |
| 19 | PASCO | 24.114 | 199 | 9 | 5 |
| 13 | LA LIBERTAD | 25.296 | 214 | 8 | 7 |
| 06 | CAJAMARCA | 33.045 | 269 | 13 | 8 |
| 02 | ANCASH | 35.962 | 290 | 13 | 10 |
| 15 | LIMA | 34.990 | 290 | 13 | 9 |
| 20 | PIURA | 36.065 | 291 | 11 | 10 |
| 10 | HUANUCO | 37.201 | 306 | 12 | 9 |
| 01 | AMAZONAS | 39.306 | 317 | 12 | 8 |
| 05 | AYACUCHO | 43.504 | 364 | 16 | 11 |
| 12 | JUNIN | 43.997 | 365 | 15 | 13 |
| 22 | SAN MARTIN | 50.961 | 420 | 17 | 15 |
| 04 | AREQUIPA | 63.256 | 538 | 20 | 17 |
| 21 | PUNO | 67.963 | 567 | 23 | 19 |
| 08 | CUSCO | 72.076 | 603 | 22 | 20 |
| 17 | MADRE DE DIOS | 85.046 | 704 | 27 | 25 |
| 25 | UCAYALI | 105.342 | 867 | 36 | 31 |
| 16 | LORETO | 375.116 | 3.054 | 122 | 97 |

## `pocos_datos` (umbral exigente: menos de 4 celdas)

| Dataset | Departamentos excluidos |
|---|---|
| IMERG | Callao |
| GPCP | Callao, Tumbes |
| POWER | Callao, Tumbes, Lambayeque |

Los departamentos costeros pierden las celdas cuyo centro cae en el mar. Afecta a POWER y GPCP, no a IMERG.
