# Registro de pruebas de: Sebastian
Fecha y hora: sábado 14 de noviembre de 2026, 10:50 a 11:40 (Lima)
Laboratorios: 0, 1 y 4 (según `12-guia-probar-datasets-peru.md`)

| Dataset | ¿Funcionó? | Tiempo | Peso del archivo | Unidades | Problemas o errores |
|---|---|---|---|---|---|
| NASA POWER | Sí | 0,6 a 1 s por consulta | ~15 KB por punto (2000–2025, 3 variables, mensual) | lluvia mm/día · T2M °C · GWETTOP 0–1 | Ninguno. Cada año trae un "mes 13" que es el promedio anual (hay que quitarlo) |
| IMERG | No probado (no es de mi lab) | — | — | — | Solo conté celdas con la grilla de 0.1° (ver lab 4) |
| MODIS MOD13A3 | No probado (no es de mi lab) | — | — | — | — |
| GeoJSON | Sí | instantáneo | 136 KB (`peru_departamental_simple.geojson`) | — | Ninguno |
| Earthdata (lab 0) | Sí, `Sesión iniciada: True` | — | — | — | Yo **no tenía cuenta**: la creé hoy. El doc 03 dice que los 4 ya tenían; hay que corregirlo |

Entorno: Python 3.14, todas las librerías de la guía se instalaron sin problemas.

## Qué encontré
- **Variables y nombres exactos que funcionaron (POWER):** `T2M`, `PRECTOTCORR`, `GWETTOP`, `RH2M` (%), `QV2M` (g/kg). La humedad del aire queda confirmada.
- **Variables que NO funcionaron:** ninguna.
- **Fuente real de POWER:** el `header` dice `sources: MERRA2` (modelo de NASA), versión de API v2.10.0, valor de relleno -999.
- **Valores -999:** 0 en Piura, Tumbes y Puno (2000–2025).
- **Departamentos con pocas celdas o sin datos:** Callao (0 en POWER, 1 en IMERG) y Tumbes (1 en POWER). Tabla completa abajo.
- **Cosas raras en los datos:** ninguna. Ver nota sobre el Caso 1.

## Respuestas a las preguntas de mis laboratorios

### Laboratorio 1: NASA POWER
1. **¿Llegaron las 3 variables?** Sí.
2. **Unidades:** `PRECTOTCORR` mm/día · `T2M` °C · `GWETTOP` adimensional (0 a 1). Vienen en `datos["parameters"][VAR]["units"]`.
3. **¿Hay -999?** No, ninguno.
4. **Piura y Tumbes frente a Puno:** el **Niño costero de 2017 se ve claro**: Piura tuvo 1,84 mm/día de media ese año (lo normal es ~0,4) y Tumbes 2,84. También destaca 2023. En 2000–2025 Puno no se seca en esos años.
   **Corrección (con el registro de Favio, 1981–2024):** el contraste del Caso 1 **sí aparece en los Niños grandes**. Puno baja a 151 mm en 1983 y a 288 mm en 1998, frente a una media de 421. El de 2017 fue un Niño **costero**, que no seca el altiplano. Conclusión: para el Caso 1 hay que usar el **periodo largo (desde 1981)**; con 2000–2025 el contraste no se ve.
   Lluvia media 2000–2025: Piura 0,42 · Tumbes 1,04 · Puno 1,22 mm/día.
5. **Humedad:** `RH2M` y `QV2M` funcionan (HTTP 200).
6. **Tiempo y 25 consultas seguidas:** 25 consultas en 17 s, sin errores ni bloqueos. Sirve para el pipeline.

Archivos (en mi laptop): `salida/power_caso1.png`, `salida/power_{piura,tumbes,puno}_anual.csv`.

### Laboratorio 4: GeoJSON y celdas por departamento
1. **Columnas:** `NOMBDEP` (nombre), `FIRST_IDDP` (ubigeo), `COUNT`, `HECTARES`. Proyección EPSG:4326.
2. **Cantidad:** 25 departamentos (Lima no viene separada en Lima Provincia).
3. **Ubigeo:** `FIRST_IDDP` ya viene como **texto con dos dígitos** (`"01"` a `"25"`): coincide con el contrato sin convertir nada. Piura = `"20"`, Puno = `"21"`, Tumbes = `"24"`, Callao = `"07"`, Lima = `"15"`.
4. **Peso:** 136 KB, liviano para el mapa; no hace falta simplificarlo.

**Celdas por departamento** (contadas por centro de celda; POWER = grilla MERRA-2 0.5° × 0.625°, IMERG = 0.1°):

| Ubigeo | Departamento | POWER | IMERG |
|---|---|---|---|
| 07 | Callao | **0** | **1** |
| 24 | Tumbes | **1** | 37 |
| 14 | Lambayeque | 3 | 118 |
| 23 | Tacna | 4 | 138 |
| 18 | Moquegua | 5 | 131 |
| 09 | Huancavelica | 5 | 186 |
| 19 | Pasco | 5 | 199 |
| 11 | Ica | 6 | 175 |
| 03 | Apurímac | 6 | 176 |
| 13 | La Libertad | 7 | 214 |
| 06 | Cajamarca | 8 | 269 |
| 01 | Amazonas | 8 | 317 |
| 15 | Lima | 9 | 290 |
| 10 | Huánuco | 9 | 306 |
| 02 | Áncash | 10 | 290 |
| 20 | Piura | 10 | 291 |
| 05 | Ayacucho | 11 | 364 |
| 12 | Junín | 13 | 365 |
| 22 | San Martín | 15 | 420 |
| 04 | Arequipa | 17 | 538 |
| 21 | Puno | 19 | 567 |
| 08 | Cusco | 20 | 603 |
| 17 | Madre de Dios | 25 | 704 |
| 25 | Ucayali | 31 | 867 |
| 16 | Loreto | 97 | 3054 |

No calculé el promedio de lluvia por departamento con IMERG porque necesita los datos del lab 2 (Josue y Leandro). El script `lab4_departamentos.py` ya tiene la máscara lista para eso.

## Lo que cambiaría en el plan (propuestas para los 4)

1. **Callao → `pocos_datos`.** No tiene celdas de POWER y solo 1 de IMERG. Propongo dejarlo con el semáforo "Pocos datos". Además, Callao es desierto costero y casi no llueve: su tendencia de lluvia diría poco aunque hubiera datos.
2. **Usar SENAMHI solo para validar, no para rellenar.** Busqué fuentes oficiales para completar Callao:
   - **PISCOp v3.0** (SENAMHI, lluvia 1981–2025, abierto): tiene la misma resolución que IMERG (0.1°), así que Callao seguiría con 1 celda. **Ojo, doc 13:** ahí se descarta PISCO porque "llega a 2016", pero eso era la v2.1; **la v3.0 llega a 2025** y se baja libre desde figshare. Sirve como segunda opinión para la lluvia en todo Perú. [Nota de SENAMHI](https://www.gob.pe/institucion/senamhi/noticias/1398654-piscop-v3-0-la-nueva-referencia-de-datos-de-precipitacion-para-la-gestion-hidrica-y-el-monitoreo-climatico-en-el-peru)
   - **Estaciones de SENAMHI**: dan datos puntuales, pero su licencia figura como "no especificada". [Datos abiertos](https://www.datosabiertos.gob.pe/dataset/datos-hidrometeorol%C3%B3gicos-de-libre-acceso)
   - Las [reglas de Space Apps](https://www.spaceappschallenge.org/legal/) permiten datos que no son de NASA solo si son abiertos y se citan.

   Si rellenamos Callao con SENAMHI y el resto con NASA, el mapa mezcla fuentes y deja de ser comparable. Propuesta: mostrar en la ficha algo como "NASA dice X; las estaciones de SENAMHI lo confirman" para Piura o Puno. Suma credibilidad sin mezclar fuentes. **No cambia el contrato.**
3. **Tumbes con POWER (1 celda):** es poco confiable. Para la lluvia del Caso 1 conviene usar IMERG (37 celdas).
4. **Corregir el doc 03:** no todos tenían cuenta Earthdata (yo la creé hoy).

## Mi postura sobre los cambios al contrato (doc 13 y registro de Josue)

Como coresponsable del contrato, apruebo para el mínimo del domingo:

| Cambio | Postura | Motivo |
|---|---|---|
| `year_start`, `year_end` en `stats` | ✅ Sí | El resultado cambia según el periodo; sin esto, la ficha confunde |
| `source` y `period` en `/api/variables` | ✅ Sí | Space Apps obliga a citar; da confianza al jurado |
| `pct_change_per_decade` | ✅ Solo para lluvia | Se entiende mejor, pero exagera donde casi no llueve: va `null` si la media es casi 0 (Lima, Callao) |
| Aviso de Josue (`lag1` > 0,5 o magnitud despreciable) | ✅ Sí | Evita mostrar como "cambio real" algo engañoso (Iquitos, Lima +0,03) |
| Dos periodos por variable | ⏳ Extra, no mínimo | Duplica datos y pantallas; en el mínimo, un periodo por variable (el de su fuente principal) |

Josue y yo cerramos los nombres exactos y rehacemos `mock_data` con estos campos. Se avisa a los 4 antes de cambiar el contrato.
