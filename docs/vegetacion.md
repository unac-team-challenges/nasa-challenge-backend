# Vegetación (NDVI): estado y límites

Resultado del Lab 3 de Favio (MODIS MOD13A3, 2001–2024, 6 zonas exploradas) y de la caja nueva de Olmos (2026-11-15). Detalle y código en `pipeline/exploracion/favio/`. Reglas que aplican: [`reglas-datos.md`](reglas-datos.md).

## Qué se confirmó
- **Chavimochic:** área verde (NDVI > 0,3) de 189 a 355 km² (+88 %); Sen +0,054 por década, p < 0,0001.
- **Ica-Villacurí:** de 118 a 222 km² (+88 %); Sen +0,027 por década, p < 0,0001.
- **Olmos (con aviso):** caja nueva sobre las tierras del proyecto. NDVI de 0,224 a 0,331; Sen +0,081 por década, IC [0,025; 0,129], `real` también contando la caja descartada (q = 0,0001). Lleva aviso porque se eligió tras descartar otra y depende de El Niño (ver abajo).
- Con esto el Caso 2, «la costa que reverdece», se sostiene con datos reales.

## Zonas descartadas o sin dato útil (decidido el 2026-11-14)
| Zona | Estado | Motivo |
|---|---|---|
| **Olmos, caja del Lab 3** | **Descartada.** Reemplazada por la caja nueva (ver abajo). | La caja (−80,00, −6,10, −79,75, −5,85) cayó sobre bosque seco natural, no sobre las tierras irrigadas del proyecto (que empezó en 2014): salía sin tendencia (p = 0,43; área verde de 737 a 589 km²). |
| **Selva (Iquitos)** | No usar NDVI. | Saturado en ~0,85 todo el periodo: no detecta cambios. Propuesta: cobertura de árboles (ver abajo). |
| **Lima** | Usar con cautela. | Pierde 13 de 288 meses por la garúa; área verde mínima (17 → 10 km²). |
| **Valle del Mantaro** | Solo informativo. | El intervalo de la tendencia incluye 0 (p = 0,027). Con el criterio único de [`tendencias.md`](tendencias.md) §2b es `posible_casualidad`. |

### Olmos con el recuadro nuevo (2026-11-15)
- **Orden de las decisiones (importa):** la caja del Lab 3 se descartó **después** de ver su resultado (p = 0,43). La caja nueva se eligió con un criterio independiente del NDVI y **antes** de ver su propio NDVI: es la de 0,25° con más campos de cultivo en OpenStreetMap (unos 4.400 polígonos `landuse=farmland/orchard`, frente a unos 150 en la caja vieja; Overpass, 2026-11-15). Para no esconder el intento fallido, **la prueba descartada se cuenta en Benjamini-Hochberg** (`PRUEBAS_DESCARTADAS` en `pipeline/ndvi.py`): Olmos sigue `real` (q = 0,0001).
- **Recuadro:** (−80,15, −6,25, −79,90, −6,00), unos 765 km². **Mezcla riego con bosque seco:** las tierras nuevas son unos 380 km², y el área verde llega a 640 km² en 2023 (El Niño).
- **Solicitud AppEEARS** `ee736bc9…` (`pipeline/exploracion/favio/scripts/lab3_olmos.py`, que reutiliza `ndvi.enviar` con solo la caja de Olmos).
- **Resultado:** NDVI de 0,224 (2001) a 0,331 (2024); Sen +0,081 por década, IC [0,025; 0,129], `real`, lag1 0,40. Área verde: **124,5 km² en 2001 y 419 km² en 2024** (los extremos que sirve la API). En promedios, 35 km² en 2001–2013 y 341 km² en 2016–2024.
- **El Niño pesa mucho:** los picos son 2017 (0,335; 457 km²) y 2023 (0,409; 640 km²), y 2016 casi no supera a 2015. Sin 2017 y 2023, la tendencia sigue (Sen +0,056, IC [0,004; 0,109]). **Sin 2015–2017 y 2023, el IC incluye 0** (Sen +0,055, IC [−0,013; 0,107]). Por eso Olmos lleva un `aviso` en `stats` que la ficha muestra.
- 2021 y 2022 tienen la misma área verde (292,8 km² = 341 píxeles) con NDVI distinto: se revisó el NetCDF, los 12 meses de cada año están bien asignados y son conjuntos de píxeles distintos (difieren en 42). Es una coincidencia.

### Cómo se retomó Olmos (histórico)
1. Mover el recuadro al sur y al oeste, sobre las tierras irrigadas del proyecto.
2. Repetir la solicitud con `scripts/lab3_appeears.py` (AppEEARS tardó ~3 h el 14-nov) y correr `lab3_analisis.py`.
3. (Hecho el 2026-11-15: ver la sección anterior.)

## La variable en el pipeline (`pipeline/ndvi.py` → `data/ndvi.json`)

- **Zonas:** Chavimochic (ubigeo 13) e Ica-Villacurí (11), con las mismas cajas del Lab 3, y Olmos (14), con la caja nueva y su aviso.
- **Unidad geográfica:** recuadro de 0,25° × 0,25° (~27 × 27 km) sobre el valle, **no** el promedio del departamento. Va escrito en cada zona (`unidad_geografica`) y la ficha debe mostrarlo.
- **Campos por año:** `ndvi_anual` (0–1) y `area_verde_km2` (píxeles con NDVI medio del año > 0,3; el promedio del píxel usa sus meses con dato confiable, como en el Lab 3). La tendencia (`stats`, con `tendencia_de: "ndvi_anual"`) se calcula sobre `ndvi_anual`; `area_verde_km2` es para el antes y después del Caso 2.
- **Años:** 2001–2024, solo con los 12 meses distintos válidos (un mes vale si al menos el 50 % de los píxeles tiene dato confiable).
- **Tendencia:** el mismo método que la temperatura: `estadisticas()`, Benjamini-Hochberg entre las zonas del archivo (más las pruebas descartadas) y `clasificar()` de `pipeline/tendencias.py` (`scipy`, `pymannkendall` y el criterio único de [`tendencias.md`](tendencias.md) §2b, con mínimo de 20 años).
- **Refresco:** a mano, una vez al año (enero): `enviar` → `estado` → `bajar` → `calcular`. `enviar` pide las 3 zonas en una sola solicitud, así que reproduce el archivo entero. AppEEARS tarda ~3 h, así que no va en el cron.

### Selva: propuesta de variable (por decidir)
**MODIS MOD44B v061** (Vegetation Continuous Fields, NASA LP DAAC): porcentaje de cobertura de árboles, anual, 250 m, desde 2000 (colección verificada en el CMR de la NASA el 2026-11-14). No se satura como el NDVI y mide justo lo que importa en la selva: pérdida de bosque. Se pediría por AppEEARS igual que el MOD13A3. Es otra variable y otro JSON (regla 3).

### En la API (2026-11-15)
- `data/ndvi.json` se generó con los NetCDF de dos solicitudes, copiados a `pipeline/cache/ndvi/` y procesados con `python pipeline/ndvi.py calcular`: la del Lab 3 (`44445de3…`) para Chavimochic e Ica, y la de Olmos (`ee736bc9…`). Una solicitud nueva con `enviar` trae las 3 zonas juntas.
- **Coincide con el Lab 3:** Chavimochic, NDVI de 0,1906 a 0,3104 y de 188,9 a 355,5 km²; Ica-Villacurí, NDVI de 0,1403 a 0,198 y de 117,6 a 221,5 km². Las dos salen `real`.
- `GET /api/vegetacion` sirve el archivo tal cual (`src/models/vegetacion.rs`). `src/data.rs` lo valida al arrancar: NDVI entre −1 y 1, ubigeo y departamento, `unidad_geografica`, recuadro y años de `stats`. Si algo no cuadra, el error dice qué zona falla.
- La serie va como en `/api/zonas/{id}`: `serie: [{anio, ndvi_anual, area_verde_km2}]`, de menor a mayor año. `p_value` y `q_value` valen como mínimo `0.000001` (la ficha muestra «< 0,000001»).
- Las fechas de los NetCDF de AppEEARS usan calendario juliano: hace falta `cftime` (ya está en `pipeline/requirements.txt` y en el lock).
- Credencial: `ndvi.py` acepta `~/_netrc`, que es como lo guarda earthaccess en Windows. Ese pudo ser el `401`/«faltan credenciales» del 14-nov.
