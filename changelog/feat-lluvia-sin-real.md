# feat/lluvia-sin-real

PR → `developer`.

## Cambiado
- `pipeline/tendencias.py`: la lluvia (solo IMERG) **nunca sale `real`**; con `q < 0.05` queda `posible_casualidad`. `pocos_datos` se mantiene. Temperatura sin cambios.
- Motivo: en 2001–2024 IMERG baja en 25 de 25 departamentos y POWER (MERRA-2) solo en 11; la razón IMERG/POWER cae de ~2,2 a ~1,6 en 2014 (cambio TRMM → GPM). El escalón del instrumento puede fingir la tendencia.
- El `aviso` de lluvia ahora dice que por eso no se marca como real.
- `data/zonas/lluvia*.json` regenerados: lluvia 0 `real`, 24 `posible_casualidad`, 1 `pocos_datos`.
- Docs (`reglas-datos.md`, `tendencias.md`), test unitario y comprobación en `tests/e2e.sh`.

## Pendiente
- Revisar cuando haya GPCP como contraste independiente (puede devolver `real` a algunas zonas).
