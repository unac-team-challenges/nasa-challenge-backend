# feat/mapa-calor-temperatura

Mapa de calor de temperatura en el frontend: la `T2M` de cada celda de NASA POWER en vez de un color plano
por departamento.

## Por qué
El promedio por departamento mezcla costa, Andes y selva: Lima sale 13,8 °C y Pasco 19,6 °C. La celda
muestra el valor donde está (costa de Lima ~18 °C, altiplano de Puno ~8 °C, Iquitos ~26 °C). Las tendencias
(°C/década) siguen por departamento: para el cambio, mezclar alturas no importa.

## Qué cambia
- `pipeline/power.py`: `celdas_json()` escribe `data/celdas/temperatura.json` con el `df` de `T2M` que ya
  baja (sin descargas extra): celdas con centro en algún departamento, años con 12 meses, `null` si falta.
- `data/celdas/temperatura.json`: 344 celdas, 2001–2024, sin huecos (59 KB).
- `GET /api/celdas?variable=temperatura` (`src/routes/api.rs`, `src/models/celdas.rs`). Otra variable → 400
  (`ApiError::SinCeldas`). Se valida al arrancar (`Datos::validar_celdas`: no vacía, dentro de Perú, años
  dentro de `variables.json`, valores en −40..50 °C) y se sirve como `Bytes` (sin volver a serializar).
- Tests: `celdas_de_temperatura`, `celdas_solo_temperatura`, `celdas_mal_formadas_se_rechazan`; checks en
  `tests/e2e.sh`. `openapi.json` regenerado.
- `docs/datos.md`: sección «Malla de temperatura» con límites y fuentes.

## Pendiente
- Ucayali (0,77 °C/década) es atípico frente a estudios andinos (0,13–0,45): revisar si es real.
- Mejora futura: PISCOt v1.2 de SENAMHI (~1 km, corrige por topografía), solo hasta 2020.
