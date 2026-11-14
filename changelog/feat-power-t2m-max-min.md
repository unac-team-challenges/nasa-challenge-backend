# feat/power-t2m-max-min

## Añadido
- `pipeline/power.py`: pide también `T2M_MAX` y `T2M_MIN` (temperatura máxima y mínima a 2 m, °C).
- `data/power.json` regenerado (2015–2020, 25 regiones). `PRECTOTCORR` y `T2M` no cambiaron; se comprobó `T2M_MIN <= T2M <= T2M_MAX` en todos los años.
- `src/models/power.rs`: `Medidas` con `t2m_max` y `t2m_min`; `tests/api.rs` los exige.
- Docs: variables nuevas y decisión «temperatura = MERRA-2 vía POWER, sin script aparte de MERRA-2».

## Aviso al equipo (contrato)
`/power/{region}` ahora devuelve 4 variables por año en vez de 2. Los campos anteriores no cambian; los clientes que ignoran campos extra no se rompen.
