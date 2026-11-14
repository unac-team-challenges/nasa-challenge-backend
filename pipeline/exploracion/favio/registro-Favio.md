# Registro de pruebas de: Favio
Fecha y hora: sábado 14 de noviembre de 2026, 11:00–12:00 (Lima); Lab 3 completado a las 14:30 (AppEEARS tardó unas 3 horas en procesar)
Laboratorios: 0 (Earthdata), 1 (NASA POWER) y 3 (MODIS MOD13A3, NDVI)

| Dataset | ¿Funcionó? | Tiempo | Peso del archivo | Unidades | Problemas o errores |
|---|---|---|---|---|---|
| Earthdata (login) | ✅ Sí, con `earthaccess.login(persist=True)` | 1 min | — | — | Ninguno |
| NASA POWER | ✅ Sí | 0,7–1,5 s por consulta; 25 departamentos en menos de 1 min | ~10–30 KB de JSON por punto | `T2M` °C · `PRECTOTCORR` mm/día · `GWETTOP` 0–1 | Ninguno. Sin valores -999 entre 1981 y 2024 |
| MODIS MOD13A3 | ✅ Sí, por la API de AppEEARS (tarea de área, 6 recuadros de ~25 × 25 km, 2001–2024) | Solicitud aceptada al instante; **procesamiento de unas 3 horas** (16:30 → 19:27 UTC) | 4 MB en total: 6 NetCDF de 0,4–0,6 MB + CSV de estadísticas y calidad | En el NetCDF el NDVI **ya viene escalado** (0 a 1); `pixel_reliability`: 0 bueno, 1 marginal, 3 nube | Ninguno. La única demora es la cola de AppEEARS |
| GeoJSON | No me tocaba | | | | |

## Qué encontré
- **Variables y nombres exactos que funcionaron (POWER):**
  - `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`;
  - `RH2M`, `QV2M`, `T2MDEW`;
  - `GWETTOP`, `GWETROOT`.
  - La fuente que declara la API es `MERRA2`.
- **Variables que NO funcionaron:** ninguna.
- **Unidades:** la lluvia viene en **mm/día** (promedio del mes). Para el total anual hay que multiplicar el promedio anual por 365. El "mes 13" es el promedio anual.
- **Departamentos con pocas celdas:** en POWER, Lima y Callao caen en la **misma celda** (dan valores idénticos).
- **Cosas raras en los datos:**
  - POWER da para Puno unos **420 mm al año**, menos que lo esperado para el altiplano, por su celda grande. Conviene usar IMERG en la ficha.
  - `GWETTOP` y `GWETROOT` vienen redondeados a 2 decimales: muchas pendientes de Sen salen en 0. **No sirven para tendencias finas.**

## Respuestas a las preguntas del Laboratorio 1
1. **¿Llegaron las 3 variables?** Sí (HTTP 200).
2. **Unidades:** °C, mm/día y 0–1 (vienen en `datos["parameters"]`).
3. **¿Valores -999?** Ninguno entre 1981 y 2024 en Piura.
4. **Piura y Tumbes frente a Puno:** la lluvia anual no se parece. Se ven los Niños de 1983, 1998 y 2017 en el norte, **y en esos mismos años Puno se seca**:

   | Año | Piura | Tumbes | Puno |
   |---|---|---|---|
   | 1983 | 386 mm | 1080 mm | 151 mm |
   | 1998 | 1367 | 2247 | 288 |
   | 2017 | 670 | 1036 | 496 |
   | Promedio 1981–2024 | 202 | 419 | 421 |

   Gráfico: `resultados/power_caso1.png` · tabla: `resultados/power_caso1_anual.csv`.
5. **Humedad:** POWER acepta `RH2M`, `QV2M` y `T2MDEW`.
6. **Tiempo:** entre 0,7 y 1,5 s por consulta. Pedí los 25 departamentos seguidos (4 en paralelo) sin errores ni bloqueos.

**Extra (vista rápida de tendencias, 25 departamentos):**
- **Temperatura:** sube con significancia (Mann-Kendall + BH) en 21 de 25 departamentos desde 1981, y en 18 desde 2000.
- **Lluvia:** el signo de la tendencia **cambia según el periodo** en Apurímac, Loreto y Piura. Detalle en `conclusiones.md` y en `14-vista-rapida-datos-14nov.md` (Drive).

## Respuestas a las preguntas del Laboratorio 3
Zonas (recuadros de ~25 × 25 km): Chavimochic (Virú-Chao), Olmos y Ica-Villacurí (valles irrigados), Lima (ciudad), selva cerca de Iquitos y valle del Mantaro (sierra). "Área verde" = píxeles de 1 km con NDVI anual > 0,3. Tendencia con `lab5_tendencias.py` de Josue (TFPW + Sen con IC95).

| Zona | NDVI 2001 → 2024 | Área verde 2001 → 2024 | Tendencia (Sen por década) | Meses perdidos por nubes |
|---|---|---|---|---|
| **Chavimochic** | 0,19 → 0,31 | **189 → 355 km² (+88 %)** | **+0,054**, p < 0,0001, IC sin 0 | 0 de 288 |
| **Ica (Villacurí)** | 0,14 → 0,20 | **118 → 222 km² (+88 %)** | **+0,027**, p < 0,0001, IC sin 0 | 0 de 288 |
| Olmos | 0,44 → 0,35 | 737 → 589 km² | +0,012, p = 0,43 (sin tendencia) | 1 de 288 |
| Lima | 0,13 → 0,14 | 17 → 10 km² | +0,005, p = 0,005 (significativa pero minúscula) | **13 de 288** (garúa invernal) |
| Selva (Iquitos) | 0,84 → 0,85 | 495 → 495 km² (todo) | +0,008 (saturada) | 8 de 288 |
| Valle del Mantaro | 0,43 → 0,45 | 477 → 468 km² | +0,011, IC incluye 0 (p = 0,03: no concuerdan, se toma el IC) | 0 de 288 |

1. **¿Cuánto tardó y cuánto pesó?** La solicitud entró al instante, pero AppEEARS tardó **unas 3 horas** en procesarla (hoy había mucha carga). El resultado pesa 4 MB.
2. **¿Se ve el valle verde contra el desierto?** **Sí, muy claro.** En Chavimochic e Ica el valle aparece verde y el desierto en amarillo, y **en 2024 hay manchas verdes nuevas** donde en 2001 había desierto (tierras irrigadas nuevas; en Ica, la pampa de Villacurí). Imagen: `resultados/lab3_antes_despues.png`.
3. **Selva y sierra: ¿meses vacíos por nubes? ¿Saturación?** Menos de lo temido. Por mes, MODIS ya combina varias pasadas: la selva perdió **8 de 288 meses** y la sierra **ninguno**. **Lima perdió 13** por la garúa de invierno. **La selva sí se satura**: el NDVI está en ~0,85 todo el tiempo y casi no cambia, así que el NDVI no sirve para ver deforestación ahí (haría falta otra variable).
4. **¿Se puede dibujar el polígono de un valle?** Sí, con recuadros simples basta para la demo. Pero **el recuadro de Olmos quedó sobre bosque seco natural** y no sobre las tierras nuevas del proyecto Olmos (que empezó en 2014), por eso no muestra tendencia. Hay que moverlo al sur y al oeste.
5. **Antes y después (2001 frente a 2024):** hay datos completos de los dos años en todas las zonas. Las imágenes de Chavimochic e Ica sirven directamente para el `react-compare-slider` del Caso 2.

**Conclusión para el producto:** el Caso 2 ("la costa que reverdece") **se sostiene con datos reales de NASA**. Chavimochic e Ica casi duplicaron su área verde entre 2001 y 2024, con tendencia significativa.

## Lo que cambiaría en el plan
- Usar los años completos **2001–2024** para IMERG y MODIS: IMERG empieza en junio de 2000 y MODIS en febrero de 2000.
- Para el Caso 2, usar Chavimochic e Ica (confirmados). Mover el recuadro de Olmos a las tierras nuevas del proyecto.
- No usar NDVI para la selva: está saturado.
- No usar la humedad del suelo de POWER como variable. Si entra una cuarta variable, que sea GLDAS-2.1 o SPEI.
- Mostrar siempre en la ficha **desde qué año** se calcula la tendencia.
