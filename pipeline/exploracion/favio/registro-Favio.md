# Registro de pruebas de: Favio
Fecha y hora: sábado 14 de noviembre de 2026, 11:00–12:00 (Lima)
Laboratorios: 0 (Earthdata), 1 (NASA POWER) y 3 (MODIS MOD13A3, NDVI)

| Dataset | ¿Funcionó? | Tiempo | Peso del archivo | Unidades | Problemas o errores |
|---|---|---|---|---|---|
| Earthdata (login) | ✅ Sí, con `earthaccess.login(persist=True)` | 1 min | — | — | Ninguno |
| NASA POWER | ✅ Sí | 0,7–1,5 s por consulta; 25 departamentos en menos de 1 min | ~10–30 KB de JSON por punto | `T2M` °C · `PRECTOTCORR` mm/día · `GWETTOP` 0–1 | Ninguno. Sin valores -999 entre 1981 y 2024 |
| MODIS MOD13A3 | (pendiente) | | | NDVI × 0,0001; -3000 = sin dato | |
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
(pendiente)

## Lo que cambiaría en el plan
- Usar los años completos **2001–2024** para IMERG y MODIS: IMERG empieza en junio de 2000 y MODIS en febrero de 2000.
- No usar la humedad del suelo de POWER como variable. Si entra una cuarta variable, que sea GLDAS-2.1 o SPEI.
- Mostrar siempre en la ficha **desde qué año** se calcula la tendencia.
