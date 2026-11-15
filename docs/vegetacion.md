# Vegetación (NDVI): estado y límites

Resultado del Lab 3 de Favio (MODIS MOD13A3, 2001–2024, 6 zonas). Detalle y código en `pipeline/exploracion/favio/`. Reglas que aplican: [`reglas-datos.md`](reglas-datos.md).

## Qué se confirmó
- **Chavimochic:** área verde (NDVI > 0,3) de 189 a 355 km² (+88 %); Sen +0,054 por década, p < 0,0001.
- **Ica-Villacurí:** de 118 a 222 km² (+88 %); Sen +0,027 por década, p < 0,0001.
- Con esto el Caso 2, «la costa que reverdece», se sostiene con datos reales.

## Zonas sin dato útil (decidido el 2026-11-14)
| Zona | Estado | Motivo |
|---|---|---|
| **Olmos** | **Resuelto el 2026-11-15 con un recuadro nuevo** (ver abajo). | El recuadro del Lab 3 (~25 × 25 km) cayó sobre bosque seco natural, no sobre las tierras irrigadas del proyecto (que empezó en 2014): salía sin tendencia (p = 0,43). |
| **Selva (Iquitos)** | No usar NDVI. | Saturado en ~0,85 todo el periodo: no detecta cambios. Propuesta: cobertura de árboles (ver abajo). |
| **Lima** | Usar con cautela. | Pierde 13 de 288 meses por la garúa; área verde mínima (17 → 10 km²). |
| **Valle del Mantaro** | Solo informativo. | El intervalo de la tendencia incluye 0 (p = 0,027). Con el criterio único de [`tendencias.md`](tendencias.md) §2b es `posible_casualidad`. |

### Olmos con el recuadro nuevo (2026-11-15)
- **Recuadro:** (−80,15, −6,25, −79,90, −6,00). Es la caja de 0,25° con más campos de cultivo en OpenStreetMap (unos 4.400 polígonos `landuse=farmland/orchard`, frente a unos 150 en la caja vieja), consultados con Overpass. **Se eligió sin mirar el NDVI**, para que la tendencia no salga «arreglada».
- **Solicitud AppEEARS** `ee736bc9…` (`pipeline/exploracion/favio/scripts/lab3_olmos.py`).
- **Resultado:** NDVI de 0,224 (2001) a 0,331 (2024); Sen +0,081 por década, IC [0,025; 0,129], `real`. El área verde media pasa de **35 km² (2001–2013) a 341 km² (2016–2024)**. El salto empieza en 2016–2017, cuando el agua del trasvase llega a las tierras nuevas, y se mantiene en años sin El Niño (2018–2022).
- **Cuidado:** en años de El Niño (2017, 2023) el bosque seco también reverdece con la lluvia, así que no todo el verde de esos años es riego. La tendencia sigue con o sin ellos.

### Cómo se retomó Olmos (histórico)
1. Mover el recuadro al sur y al oeste, sobre las tierras irrigadas del proyecto.
2. Repetir la solicitud con `scripts/lab3_appeears.py` (AppEEARS tardó ~3 h el 14-nov) y correr `lab3_analisis.py`.
3. Mientras tanto la ficha de Olmos muestra «sin dato», nunca un valor del recuadro actual.

## La variable en el pipeline (`pipeline/ndvi.py` → `data/ndvi.json`)

- **Zonas:** Chavimochic (ubigeo 13) e Ica-Villacurí (11). Son las mismas cajas del Lab 3.
- **Unidad geográfica:** recuadro de 0,25° × 0,25° (~27 × 27 km) sobre el valle, **no** el promedio del departamento. Va escrito en cada zona (`unidad_geografica`) y la ficha debe mostrarlo.
- **Campos por año:** `ndvi_anual` (0–1) y `area_verde_km2` (píxeles con NDVI medio del año > 0,3; el promedio del píxel usa sus meses con dato confiable, como en el Lab 3). La tendencia (`stats`, con `tendencia_de: "ndvi_anual"`) se calcula sobre `ndvi_anual`; `area_verde_km2` es para el antes y después del Caso 2.
- **Años:** 2001–2024, solo con los 12 meses distintos válidos (un mes vale si al menos el 50 % de los píxeles tiene dato confiable).
- **Tendencia:** el mismo método que la temperatura: `estadisticas()`, Benjamini-Hochberg entre las zonas del archivo y `clasificar()` de `pipeline/tendencias.py` (`scipy`, `pymannkendall` y el criterio único de [`tendencias.md`](tendencias.md) §2b, con mínimo de 20 años).
- **Refresco:** a mano, una vez al año (enero): `enviar` → `estado` → `bajar` → `calcular`. AppEEARS tarda ~3 h, así que no va en el cron.

### Selva: propuesta de variable (por decidir)
**MODIS MOD44B v061** (Vegetation Continuous Fields, NASA LP DAAC): porcentaje de cobertura de árboles, anual, 250 m, desde 2000 (colección verificada en el CMR de la NASA el 2026-11-14). No se satura como el NDVI y mide justo lo que importa en la selva: pérdida de bosque. Se pediría por AppEEARS igual que el MOD13A3. Es otra variable y otro JSON (regla 3).

### En la API (2026-11-15)
- `data/ndvi.json` se generó con los NetCDF de la solicitud del Lab 3 (`44445de3…`, mismas cajas que `ZONAS` en `pipeline/ndvi.py`), copiados a `pipeline/cache/ndvi/` y procesados con `python pipeline/ndvi.py calcular`. No hizo falta pedir de nuevo a AppEEARS.
- **Coincide con el Lab 3:** Chavimochic, NDVI de 0,1906 a 0,3104 y de 188,9 a 355,5 km²; Ica-Villacurí, NDVI de 0,1403 a 0,198 y de 117,6 a 221,5 km². Las dos salen `real`.
- `GET /api/vegetacion` sirve el archivo tal cual (`src/models/vegetacion.rs`). `src/data.rs` lo valida al arrancar: NDVI entre −1 y 1, ubigeo y departamento, `unidad_geografica`, recuadro y años de `stats`. Si algo no cuadra, el error dice qué zona falla.
- La serie va como en `/api/zonas/{id}`: `serie: [{anio, ndvi_anual, area_verde_km2}]`, de menor a mayor año. `p_value` y `q_value` valen como mínimo `0.000001` (la ficha muestra «< 0,000001»).
- Las fechas de los NetCDF de AppEEARS usan calendario juliano: hace falta `cftime` (ya está en `pipeline/requirements.txt` y en el lock).
- Credencial: `ndvi.py` acepta `~/_netrc`, que es como lo guarda earthaccess en Windows. Ese pudo ser el `401`/«faltan credenciales» del 14-nov.
