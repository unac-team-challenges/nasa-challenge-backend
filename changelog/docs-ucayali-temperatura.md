# docs/ucayali-temperatura

Cierra el pendiente de Ucayali que dejó `feat/mapa-calor-temperatura` (#62). Solo documentación: no cambia datos, API ni OpenAPI.

## Qué cambia
- `docs/datos.md`: sección «Ucayali: la tendencia más alta» con la comparación 2001–2024, 2001–2022 y 2001–2019 frente a Huánuco, Pasco, Loreto, San Martín y Madre de Dios, y lo que se puede y no se puede concluir.
- La frase «pendiente revisar» de «Límites conocidos» ahora apunta a esa sección.

## Conclusión
- No es una celda mala (27 de 31 celdas suben más de 0,5 °C/década) y hay coherencia con Huánuco y Pasco.
- Pesan 2023 y 2024 (28,2 y 28,5 °C): sin ellos la pendiente baja de 0,77 a 0,58, aún la más alta de la selva baja.
- Con estos datos no se separa calentamiento real, calor extremo de 2023–2024 y cambio del reanálisis.

## Pendiente (decisión del equipo)
- ¿Aviso propio para Ucayali? Hoy `tendencias.py` solo admite avisos por variable. Si se quiere, es otro PR: mecanismo por zona, texto y regenerar `data/zonas/temperatura.json`.
- Contrastar con una fuente independiente (SENAMHI, ERA5-Land o MODIS LST).
