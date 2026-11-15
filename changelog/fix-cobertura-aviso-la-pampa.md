# fix/cobertura-aviso-la-pampa

Punto 3 de lo que dejó Leandro al mezclar el #57 (revisión del #55).

## Decisión (Favio)
La Pampa tiene q < 0,001 e IC [−17,5; −12,5], pero lag1 = 0,58 porque la serie se mantiene cerca del 75 % hasta 2008 y cae desde 2009. **No se cambia el umbral** ni se calcula una tendencia «desde 2009»: ese corte se elegiría después de ver la serie. En cambio, La Pampa lleva un aviso propio que lo explica.

## Qué cambia
- `pipeline/cobertura.py`: `AVISOS` (como en `ndvi.py`) y `con_estado` se lo pasa a `clasificar()`. El texto se arma con la serie (el % de 2001–2008 y el último año), así que no queda viejo si se regenera con un año nuevo. El 2009 solo describe lo que se ve; no es un corte con el que se calcule nada. El aviso de La Pampa va delante del de lag1:
  > La pérdida no fue pareja: de 2001 a 2008 la cobertura se mantuvo cerca del 75 % y desde 2009 baja casi cada año, hasta 46 % en 2024. La caída es grande y su rango probable no incluye 0, pero como empezó de golpe una recta la describe mal, y el criterio único no la marca como cambio real.
- `data/cobertura_arboles.json` regenerado: solo cambia `stats.aviso` de La Pampa. El status (`posible_casualidad`) y los números son los mismos.
- La autoprueba y `tests/api.rs` comprueban que La Pampa lleve el aviso del quiebre.
- `docs/vegetacion.md`: la decisión y por qué no se cortó en 2009.
