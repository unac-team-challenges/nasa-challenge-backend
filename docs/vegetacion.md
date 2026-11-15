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

### Selva: cobertura de árboles en la API (2026-11-15)
`pipeline/cobertura.py` → `data/cobertura_arboles.json` → `GET /api/cobertura-arboles`. MODIS **MOD44B v061** (porcentaje de cobertura de árboles, anual, 250 m), pedido a AppEEARS (tarea `47c3f635…`). Bosque = píxel con 30 % o más de árboles (umbral de Global Forest Watch). Mismo criterio único de tendencia (`clasificar()`).

| Zona | Árboles 2001 → 2024 | Bosque 2001 → 2024 | Tendencia |
|---|---|---|---|
| **La Pampa** (Madre de Dios, minería de oro) | 74,1 % → 45,9 % | 724 → 462 km² (−36 %) | −15,3 puntos por década, IC [−17,5; −12,5], q < 0,001, pero **lag1 = 0,58**: queda `posible_casualidad` con aviso |
| **Selva cerca de Iquitos** (contraste) | 76,7 % → 79,7 % | casi todo el recuadro (491 de 491 km²) | +1,3 puntos por década, p = 0,064, IC [−0,2; +2,9]: **no distinguible de 0**, `posible_casualidad` |

- **Recuadros:** La Pampa se centró en el poblado (OpenStreetMap: −12,962, −70,001), el foco de minería 2014–2018 que reporta MAAP. Iquitos es el mismo recuadro del Lab 3.
- **Área:** el ráster de AppEEARS está en grados, así que el área de cada píxel se calcula por fila de latitud, con el largo real de un grado de latitud y de longitud en el elipsoide WGS84 (`km_por_grado`). Un año con huecos extrapola el bosque a toda la tierra según la fracción con dato, para no meter escalones falsos en la serie de km².
- **Iquitos no sirve como contraste de área:** casi todo su recuadro supera el 30 % de árboles en todos los años, así que el área queda en el tope. El contraste es la tendencia: La Pampa baja con claridad e Iquitos no muestra un cambio distinguible de 0.
- **Ojo con La Pampa:** la caída es clara y empieza hacia 2010, con la Interoceánica y la minería. Pero no es lineal: estable hasta 2009 y luego baja fuerte. Por eso los residuos quedan autocorrelacionados (lag1 0,58) y el criterio único la deja en `posible_casualidad`. No se cambió el umbral; si el equipo quiere tratar los quiebres de otra forma (por ejemplo, desde 2009), es una decisión de `tendencias.md`.

### Selva: por qué no NDVI (propuesta original)
**MODIS MOD44B v061** (Vegetation Continuous Fields, NASA LP DAAC): porcentaje de cobertura de árboles, anual, 250 m, desde 2000 (colección verificada en el CMR de la NASA el 2026-11-14). No se satura como el NDVI y mide justo lo que importa en la selva: pérdida de bosque. Se pediría por AppEEARS igual que el MOD13A3. Es otra variable y otro JSON (regla 3).

### En la API (2026-11-15)
- `data/ndvi.json` se generó con los NetCDF de la solicitud del Lab 3 (`44445de3…`, mismas cajas que `ZONAS` en `pipeline/ndvi.py`), copiados a `pipeline/cache/ndvi/` y procesados con `python pipeline/ndvi.py calcular`. No hizo falta pedir de nuevo a AppEEARS.
- **Coincide con el Lab 3:** Chavimochic, NDVI de 0,1906 a 0,3104 y de 188,9 a 355,5 km²; Ica-Villacurí, NDVI de 0,1403 a 0,198 y de 117,6 a 221,5 km². Las dos salen `real`.
- `GET /api/vegetacion` sirve el archivo tal cual (`src/models/vegetacion.rs`). `src/data.rs` lo valida al arrancar: NDVI entre −1 y 1, ubigeo y departamento, `unidad_geografica`, recuadro y años de `stats`. Si algo no cuadra, el error dice qué zona falla.
- La serie va como en `/api/zonas/{id}`: `serie: [{anio, ndvi_anual, area_verde_km2}]`, de menor a mayor año. `p_value` y `q_value` valen como mínimo `0.000001` (la ficha muestra «< 0,000001»).
- Las fechas de los NetCDF de AppEEARS usan calendario juliano: hace falta `cftime` (ya está en `pipeline/requirements.txt` y en el lock).
- Credencial: `ndvi.py` acepta `~/_netrc`, que es como lo guarda earthaccess en Windows. Ese pudo ser el `401`/«faltan credenciales» del 14-nov.
