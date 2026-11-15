# feat/vegetacion-2001-2024

Completa la malla de vegetación (NDVI de MODIS) con los 24 años, 2001–2024. Es el pendiente de `feat/malla-vegetacion`
(#70), que se mezcló con 2001–2012 porque AppEEARS aún no entregaba los bloques 2013–2018 y 2019–2024.

## Cambiado
- `data/celdas/vegetacion.json`: 1 702 celdas de 0,25° con 2001–2024 (308 KB; ~70 KB con gzip). Mismas celdas que antes.
- `data/ndvi_departamentos.json`, `data/zonas/vegetacion.json` y `data/zonas/vegetacion/*.json` regenerados
  (`calcular` → `tendencias.py`). Con 24 años ya hay tendencia: 14 cambio real, 10 posible casualidad y Callao con
  pocos datos (1 celda). Desaparecen las notas de «serie de solo N años».
- `data/variables.json`: `vegetacion` con `anio_fin` 2024.
- `tests/e2e.sh`: vuelve a exigir 2001–2024 a todas las variables (se quita el `shortcut:` de #70) y suma un check de
  `celdas/vegetacion.json`.
- `docs/datos.md`: la nota de serie corta queda solo para refrescos incompletos; resultado 2001–2024.

## Cobertura y tendencia de las 25 regiones (criterio de la tarea: celdas con dato en 15 años o más)

| Región | Celdas (≥ 15 años) | NDVI medio | Cambio por década | Estado |
|---|---|---|---|---|
| Amazonas | 52 | 0,807 | +0,005 | cambio real |
| Áncash | 47 | 0,342 | +0,014 | cambio real |
| Apurímac | 28 | 0,422 | +0,009 | posible casualidad |
| Arequipa | 83 | 0,149 | +0,009 | cambio real |
| Ayacucho | 60 | 0,356 | +0,016 | cambio real |
| Cajamarca | 44 | 0,605 | +0,015 | cambio real |
| Callao | 1 ⚠️ | 0,123 | -0,004 | pocos datos |
| Cusco | 97 | 0,623 | +0,006 | cambio real |
| Huancavelica | 29 | 0,376 | +0,014 | cambio real |
| Huánuco | 47 | 0,697 | +0,002 | posible casualidad |
| Ica | 31 | 0,115 | +0,013 | cambio real |
| Junín | 60 | 0,656 | +0,004 | posible casualidad |
| La Libertad | 31 | 0,362 | +0,016 | cambio real |
| Lambayeque | 18 | 0,287 | +0,016 | posible casualidad |
| Lima | 48 | 0,254 | +0,015 | cambio real |
| Loreto | 490 | 0,834 | +0,004 | cambio real |
| Madre de Dios | 112 | 0,846 | +0,000 | posible casualidad |
| Moquegua | 19 | 0,119 | +0,007 | cambio real |
| Pasco | 31 | 0,746 | +0,003 | posible casualidad |
| Piura | 47 | 0,363 | +0,014 | posible casualidad |
| Puno | 94 | 0,447 | +0,003 | posible casualidad |
| San Martín | 68 | 0,816 | -0,001 | posible casualidad |
| Tacna | 23 | 0,113 | +0,006 | cambio real |
| Tumbes | 5 | 0,498 | +0,009 | posible casualidad |
| Ucayali | 137 | 0,840 | +0,003 | cambio real |

- **Justas:** Callao (1 celda propia, lleva `nota` y queda en pocos datos), Tumbes (5), Lambayeque (18) y Moquegua (19).
  Las tres últimas superan el mínimo de 4.
- **Sanidad:** selva alta (Loreto 0,83, Ucayali 0,84, Madre de Dios 0,85); costa y sur bajos (Ica 0,12, Tacna 0,11,
  Moquegua 0,12, Arequipa 0,15).
- **Lectura:** las 14 regiones con cambio real suben (más verde). En la selva el aumento es mínimo (+0,003 a +0,005 por
  década) porque el NDVI está saturado: no indica que no se pierda bosque (ver `/api/cobertura-arboles`). El aviso de
  saturación de `tendencias.py` va en esas zonas.

## Cómo se generó
```bash
python pipeline/vegetacion_malla.py estado      # 4 bloques en «done»
python pipeline/vegetacion_malla.py bajar
python pipeline/vegetacion_malla.py calcular
python pipeline/tendencias.py
bash tests/e2e.sh                                # TODO OK
```
