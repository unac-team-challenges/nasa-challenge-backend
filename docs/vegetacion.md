# Vegetación (NDVI): estado y límites

Resultado del Lab 3 de Favio (MODIS MOD13A3, 2001–2024, 6 zonas). Detalle y código en `pipeline/exploracion/favio/`. Reglas que aplican: [`reglas-datos.md`](reglas-datos.md).

## Qué se confirmó
- **Chavimochic:** área verde (NDVI > 0,3) de 189 a 355 km² (+88 %); Sen +0,054 por década, p < 0,0001.
- **Ica-Villacurí:** de 118 a 222 km² (+88 %); Sen +0,027 por década, p < 0,0001.
- Con esto el Caso 2, «la costa que reverdece», se sostiene con datos reales.

## Zonas sin dato útil (decidido el 2026-11-14)
| Zona | Estado | Motivo |
|---|---|---|
| **Olmos** | **Sin dato por ahora. No usar en el producto.** | El recuadro de ~25 × 25 km cayó sobre bosque seco natural, no sobre las tierras irrigadas del proyecto (que empezó en 2014). Sale sin tendencia (p = 0,43) y el área verde baja de 737 a 589 km², lo que **engañaría** si se muestra como «sin reverdecimiento». |
| **Selva (Iquitos)** | No usar NDVI. | Saturado en ~0,85 todo el periodo: no detecta cambios. Propuesta: cobertura de árboles (ver abajo). |
| **Lima** | Usar con cautela. | Pierde 13 de 288 meses por la garúa; área verde mínima (17 → 10 km²). |
| **Valle del Mantaro** | Solo informativo. | El intervalo de la tendencia incluye 0 (p = 0,027). Con el criterio único de [`tendencias.md`](tendencias.md) §2b es `posible_casualidad`. |

### Para retomar Olmos
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
- Las fechas de los NetCDF de AppEEARS usan calendario juliano: hace falta `cftime` (ya está en `pipeline/requirements.txt` y en el lock).
- Credencial: `ndvi.py` acepta `~/_netrc`, que es como lo guarda earthaccess en Windows. Ese pudo ser el `401`/«faltan credenciales» del 14-nov.
