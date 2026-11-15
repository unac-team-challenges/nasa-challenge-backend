# feat/malla-vegetacion

Malla de vegetación (NDVI de MODIS) en las 25 regiones y malla de lluvia, para pintar el mapa como ya se pinta la
temperatura. Tarea: «vegetación en las 25 regiones, para pintar el mapa».

> **Datos reales parciales (2001–2012), por fuera del alcance de este PR completar 2013–2024.** AppEEARS entregó 2 de
> los 4 bloques de años; 2013–2018 sigue en proceso y 2019–2024 en cola en la NASA (horas o días, sin fecha que
> dependa del equipo). Nada es inventado: la malla llega hasta el último año descargado y el contrato, los tests y el
> frontend ya funcionan con cualquier `anio_fin`. Completar es solo datos: `bajar` → `calcular` → `tendencias.py`.

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

## Cobertura de las 25 regiones (con los 12 años descargados)

Celdas con dato en los 12 años (con la serie parcial, «15 años o más» de la tarea se vuelve «todos los años leídos»);
NDVI medio 2001–2012. Callao tiene 1 celda propia (lleva `nota`). Tumbes (5), Lambayeque (17) y Moquegua (19) quedan
justas pero sobre el mínimo de 4. La tabla con el criterio original (≥ 15 años) se publica cuando llegue 2013–2018.

| Región | Celdas (≥ 12 años) | NDVI medio |
|---|---|---|
| Amazonas | 52 | 0,803 |
| Áncash | 47 | 0,334 |
| Apurímac | 28 | 0,417 |
| Arequipa | 83 | 0,143 |
| Ayacucho | 60 | 0,348 |
| Cajamarca | 44 | 0,596 |
| Callao | 1 ⚠️ | 0,126 |
| Cusco | 97 | 0,618 |
| Huancavelica | 29 | 0,367 |
| Huánuco | 47 | 0,695 |
| Ica | 31 | 0,107 |
| Junín | 56 | 0,643 |
| La Libertad | 31 | 0,352 |
| Lambayeque | 17 | 0,289 |
| Lima | 48 | 0,245 |
| Loreto | 490 | 0,831 |
| Madre de Dios | 112 | 0,844 |
| Moquegua | 19 | 0,114 |
| Pasco | 31 | 0,743 |
| Piura | 47 | 0,357 |
| Puno | 94 | 0,445 |
| San Martín | 68 | 0,815 |
| Tacna | 23 | 0,109 |
| Tumbes | 5 | 0,494 |
| Ucayali | 137 | 0,837 |

Sanidad: selva alta como se esperaba (Loreto 0,83, Ucayali 0,84, Madre de Dios 0,84) y costa y sur bajos (Ica 0,11,
Tacna 0,11, Moquegua 0,11, Arequipa 0,14).

## Decisiones
- **6 meses válidos por píxel en vez de 12:** con 12 de 12 la selva queda vacía por las nubes. Va en la `nota`.
- **Variable NDVI** (no % de árboles), como recomienda la tarea; la saturación de la selva va en la `nota` y en el aviso.
- **`t2m` se queda en temperatura** y las mallas nuevas usan `valor`, como propone la tarea.

## Cambiado tras la revisión
- Malla y tendencias regeneradas con 2001–2012 (antes 2001–2006).
- Con menos de 20 años, cada departamento de `zonas/vegetacion.json` lleva una `nota` con los años que tiene: el motivo
  real de `pocos_datos` (antes no llevaba nota y fallaba `pocos_datos_lleva_nota`).
- `tests/e2e.sh`: el periodo de la vegetación se compara con el `anio_fin` de su malla (lluvia y temperatura siguen
  exigiendo 2001–2024).
- `docs/datos.md`: la lluvia va en mm/día en `/api/zonas` y en mm/año en `/api/celdas`; el frontend lee la `unidad` de
  cada respuesta.

## Pendiente (PR aparte, solo datos)
- Bajar 2013–2018 y 2019–2024 cuando AppEEARS termine, regenerar y volver a exigir 2024 en `tests/e2e.sh` (marcado con
  `shortcut:`). Publicar la tabla de cobertura con ≥ 15 años.
- Confirmar como equipo el mínimo de 6 meses sin nubes por píxel (la tarea decía 12).
