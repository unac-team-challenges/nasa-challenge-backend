# docs/ucayali-temperatura

Cierra el pendiente de Ucayali que dejó `feat/mapa-calor-temperatura` (#62): revisión de su tendencia y aviso propio. No cambia el status ni los números; solo `stats.aviso` de Ucayali.

## Qué cambia
- `pipeline/tendencias.py`: `avisos_zona` (ubigeo → función) en la variable `temperatura`, con `aviso_ucayali()`. El aviso va delante del de lag1 y sus números (los dos últimos años, la pendiente sin ellos) salen de la serie, así que no quedan viejos al regenerar.
- `data/zonas/temperatura.json` y `data/zonas/temperatura/25.json` regenerados: **solo** cambia `stats.aviso` de Ucayali (`status: real` y los números, igual).
- Tests: `test_aviso_de_ucayali_sale_de_la_serie` (Python), `ucayali_lleva_aviso_propio_en_temperatura_y_el_resto_no` (Rust) y un check en `tests/e2e.sh`.
- `docs/datos.md`: sección «Ucayali: la tendencia más alta» con la comparación 2001–2024, 2001–2022 y 2001–2019 y lo que se puede y no se puede concluir. `docs/tendencias.md` menciona el aviso por zona.

## Conclusión de la revisión
- No es una celda mala (27 de 31 celdas suben más de 0,5 °C/década) y hay coherencia con Huánuco y Pasco.
- Pesan 2023 y 2024 (28,2 y 28,5 °C): sin ellos la pendiente baja de 0,77 a 0,58, aún la más alta de la selva baja.
- Con estos datos no se separa calentamiento real, calor extremo de 2023–2024 y cambio del reanálisis.

## Pendiente
- **Frontend:** en inglés, `avisoFijo` solo mira la variable y el lag1, no la zona: la ficha de Ucayali mostraría este aviso en español. Hace falta una traducción por zona (otro PR del front).
- Contrastar con una fuente independiente (SENAMHI, ERA5-Land o MODIS LST).
