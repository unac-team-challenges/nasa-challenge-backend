# fix/vegetacion-malla-pendientes

PR: base `developer`. Pendientes menores de la revisión de #70 (`pipeline/vegetacion_malla.py`). Los datos publicados no cambian.

## Cambiado
- `anios_de`: la base conserva su hora y los tiempos van en segundos con decimales (antes se cortaba a días y se descartaba la hora de la base, que podía mover un tiempo al año vecino). Acepta `seconds`, `minutes`, `hours` y `days`; una unidad desconocida da un `ValueError` que dice cuál es, en vez de un `KeyError` sin contexto.
- `por_departamento`: Callao toma la celda más cercana **con todos los años**; una celda con huecos lo dejaba con menos años que Lima. Con la malla real la más cercana ya es completa (−11,875, −77,125), así que `ndvi_departamentos.json` queda igual.
- `autoprueba`: casos nuevos para los dos cambios (cruce de año con hora y decimales, `minutes`, unidad desconocida, Callao con la celda cercana incompleta).

## No se hizo (a propósito)
- `power.py` × 365 sin ponderar los días de cada mes: es la convención documentada (mm/día × 365 = mm/año) y la copia del frontend coincide celda por celda; cambiarla movería todos los valores de lluvia ~0,3 % y exigiría regenerar con 8 llamadas a POWER.
- `Celda` con `t2m` y `valor` como `Option`: `validar_celdas` ya exige uno solo y falla al arrancar; un enum cambiaría `openapi.json` y los tipos del frontend por un estado que ya no puede llegar.

## Pruebas
`bash tests/e2e.sh`: todo OK.
