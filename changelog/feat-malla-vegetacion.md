# feat/malla-vegetacion

Malla de vegetación (NDVI de MODIS) en las 25 regiones y malla de lluvia, para pintar el mapa como ya se pinta la
temperatura. Tarea: «vegetación en las 25 regiones, para pintar el mapa».

> **Estado: borrador con datos reales parciales (2001–2006).** AppEEARS entregó 1 de los 4 bloques de años; los otros
> tres (2007–2024) siguen en proceso. Nada es inventado: la malla llega hasta el último año descargado. Al completar se
> corre `bajar` → `calcular` → `tendencias.py` y se actualiza este PR.

## Añadido
- `pipeline/vegetacion_malla.py`: NDVI mensual de MODIS MOD13A3 v061 (1 km) vía AppEEARS para todo el Perú, en 4
  solicitudes de 6 años. Por píxel: meses con `pixel_reliability` 0 o 1 (sin nubes, nieve ni agua), año válido con al
  menos 6 meses. Por celda de 0,25°: media de píxeles si son al menos la mitad. Escribe
  `data/celdas/vegetacion.json` (formato de `temperatura.json`, campo `valor`, 3 decimales, `null` si falta el año,
  ninguna celda toda `null`, solo celdas con centro en un departamento) y `data/ndvi_departamentos.json`.
  Imprime la tabla región → celdas → NDVI medio. `autoprueba` sin red (meses, celdas, mar, `null`, departamentos,
  tiempo en segundos o días).
- `pipeline/power.py`: `data/celdas/lluvia.json` (PRECTOTCORR × 365 = mm/año, campo `valor`) con las mismas celdas;
  `python pipeline/power.py celdas` regenera solo las mallas. La de temperatura sale idéntica.
- `pipeline/tendencias.py`: variable `vegetacion` (desde `ndvi_departamentos.json`, unidad NDVI) con aviso de
  saturación si el NDVI medio es ≥ 0,75.
- API: `Variable::Vegetacion`; `GET /api/zonas?variable=vegetacion`, `/api/zonas/{id}?variable=vegetacion` y
  `GET /api/celdas?variable={lluvia,temperatura,vegetacion}` (`lluvia_imerg` → 400). `validar_celdas` por variable:
  unidad (°C, mm/año, NDVI), campo (`t2m` o `valor`, nunca los dos) y rango (−40..50, 0..12 000, −0,2..1).
  `Malla` admite `nota`. `data/variables.json` y `openapi.json` regenerados.
- Tests: `celdas_de_lluvia` y `celdas_de_vegetacion` con cifras reales (Iquitos > 2 000 mm/año y NDVI > 0,7; Ica
  < 100 mm/año y NDVI < 0,2), `celdas_sin_malla_dan_400`, `mallas_nuevas_mal_formadas_se_rechazan` (vacía, unidad
  vacía, fuera de Perú, toda `null`, fuera de rango, campo equivocado; rango por variable); los recorridos por
  variable incluyen `vegetacion`. `tests/test_tendencias.py`: aviso de saturación. Checks nuevos en `tests/e2e.sh`.
- Docs: «Malla de lluvia» y «Malla de vegetación» en `docs/datos.md`; sección en `docs/vegetacion.md`; README y CLAUDE.md.

## Cobertura de las 25 regiones (con los 6 años descargados)

Celdas con dato en los 6 años; NDVI medio 2001–2006. Callao tiene 1 celda propia (lleva `nota` de pocas celdas).
Tumbes (5), Lambayeque (18) y Moquegua (19) quedan justas pero sobre el mínimo de 4.


| Región | Celdas (≥ 6 años) | NDVI medio |
|---|---|---|
| Amazonas | 52 | 0,803 |
| Áncash | 47 | 0,327 |
| Apurímac | 28 | 0,417 |
| Arequipa | 83 | 0,141 |
| Ayacucho | 60 | 0,345 |
| Cajamarca | 44 | 0,588 |
| Callao | 1 ⚠️ | 0,127 |
| Cusco | 97 | 0,619 |
| Huancavelica | 29 | 0,363 |
| Huánuco | 47 | 0,697 |
| Ica | 31 | 0,101 |
| Junín | 56 | 0,643 |
| La Libertad | 31 | 0,343 |
| Lambayeque | 18 | 0,273 |
| Lima | 48 | 0,238 |
| Loreto | 490 | 0,832 |
| Madre de Dios | 112 | 0,846 |
| Moquegua | 19 | 0,114 |
| Pasco | 31 | 0,745 |
| Piura | 47 | 0,351 |
| Puno | 94 | 0,447 |
| San Martín | 68 | 0,818 |
| Tacna | 23 | 0,108 |
| Tumbes | 5 | 0,476 |

Sanidad: selva alta como se esperaba (Loreto 0,83, Ucayali 0,84, Madre de Dios 0,85) y costa y sur bajos (Ica 0,10,
Tacna 0,11, Moquegua 0,11, Arequipa 0,14).

## Decisiones
- **6 meses válidos por píxel en vez de 12:** con 12 de 12 la selva queda vacía por las nubes. Va en la `nota`.
- **Variable NDVI** (no % de árboles), como recomienda la tarea; la saturación de la selva va en la `nota` y en el aviso.
- **`t2m` se queda en temperatura** y las mallas nuevas usan `valor`, como propone la tarea.

## Pendiente
- Bajar los bloques 2007–2012, 2013–2018 y 2019–2024 cuando AppEEARS termine y regenerar. Hasta entonces fallan, por
  la serie parcial y no por el código: `pocos_datos_lleva_nota` (las 25 zonas son `pocos_datos` con 6 años) y los
  checks de periodo 2001–2024 de `tests/e2e.sh`.
- Avisar a Leandro para `pnpm gen` y la variable en el frontend (hay una rama local de prueba, `feat/vegetacion-mapa`).
