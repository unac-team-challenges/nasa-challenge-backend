# fix/ndvi-olmos-texto

Pendiente que dejó Leandro al aprobar el #56 (Olmos en el Caso 2).

## Qué cambia
- **`tipo` y `unidad_geografica` de Olmos** ya no dicen «valle irrigado», que contradecía su aviso. Ahora:
  - `tipo`: «riego nuevo y bosque seco»;
  - `unidad_geografica`: «recuadro de 0,25° × 0,25° (~27 × 27 km) sobre las tierras nuevas del proyecto, que mezcla riego y bosque seco; no es el promedio del departamento».
  - Chavimochic e Ica no cambian.
- `pipeline/ndvi.py`: `UNIDAD_GEO_ZONA` con el texto propio de Olmos (las demás zonas usan `UNIDAD_GEO`). La autoprueba comprueba que Olmos diga «bosque seco», no diga «valle irrigado» y siga diciendo «no es el promedio del departamento».
- `data/ndvi.json` regenerado con `python pipeline/ndvi.py calcular`: solo cambian esas dos líneas de Olmos; los números son los mismos.
- `tests/api.rs`: Olmos no puede tener `tipo` «valle irrigado» y su `unidad_geografica` debe decir «bosque seco».
- `src/models/vegetacion.rs` y `docs/vegetacion.md`: el ejemplo de `tipo` y la unidad de Olmos.

## Comprobado
- El check `ndvi.json: unidad geográfica explícita` («no es el promedio del departamento») sigue pasando.
- El segundo punto de Leandro (que `stats.aviso` se vea en la ficha) es del frontend: se verifica al integrar Olmos en el Caso 2.

## Detalles de documentación (revisión del #58)
- `pipeline/ndvi.py`: el docstring ya no dice «solo los valles irrigados»; nombra Chavimochic e Ica como valles y Olmos como tierras nuevas con aviso.
- `docs/vegetacion.md`: «sobre el valle» queda acotado a Chavimochic e Ica.
