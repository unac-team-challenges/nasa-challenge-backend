# feat/ndvi-olmos

PR: base `developer`. Autor: Favio. Es la parte 2 de la tarea de vegetación (Olmos).

## Añadido
- **Olmos** es la tercera zona de `data/ndvi.json` y de `/api/vegetacion`, con el recuadro movido a las tierras nuevas del proyecto: (−80,15, −6,25, −79,90, −6,00).
  - Es la caja de 0,25° con más campos de cultivo en OpenStreetMap (unos 4.400 frente a unos 150 en la caja vieja). Se eligió antes de ver su propio NDVI, pero **después** de descartar la caja del Lab 3 por su resultado.
  - NDVI de 0,224 a 0,331; Sen +0,081 por década, IC [0,025; 0,129], **real**.
  - Área verde: 124,5 km² en 2001 y 419 km² en 2024 (los extremos que sirve la API). En promedios, 35 km² en 2001–2013 y 341 km² en 2016–2024.
- `pipeline/exploracion/favio/scripts/lab3_olmos.py`: la solicitud a AppEEARS (tarea `ee736bc9…`).

## Cambiado
- `pipeline/ndvi.py`: Olmos en `ZONAS` y la documentación de las zonas al día.
- `data/ndvi.json` regenerado. Chavimochic e Ica no cambian; con 3 zonas, Benjamini-Hochberg sigue dándolas reales.
- `tests/api.rs`: el test de `/api/vegetacion` revisa las 3 zonas con sus cifras de 2001 y 2024.
- `docs/vegetacion.md`: Olmos pasa de «sin dato» a resuelto, con el detalle y el cuidado con los años de El Niño.

## Pendiente
- Frontend: mostrar Olmos en el Caso 2 (ficha de Lambayeque) desde `/api/vegetacion`.

## Ajustes tras la revisión de Leandro
- **Respuesta a la pregunta:** la caja del Lab 3 se descartó *después* de ver su resultado (p = 0,43). La caja nueva se eligió con OpenStreetMap antes de ver su propio NDVI. Decisión de Favio: Olmos queda `real`, pero con aviso, y **la prueba descartada se cuenta en Benjamini-Hochberg** (`PRUEBAS_DESCARTADAS = [0.4282]`). Olmos sigue real (q de 7,4e-05 a 9,9e-05); Chavimochic e Ica no cambian.
- **Aviso en `stats.aviso` de Olmos** (`AVISOS` en `ndvi.py`): la caja se movió tras descartar otra, mezcla riego con bosque seco, y sin los años de El Niño (2015–2017 y 2023) el rango probable incluye 0. Comprobado: sin 2017 y 2023 el IC es [0,004; 0,109]; sin 2015–2017 y 2023, [−0,013; 0,107].
- **`pipeline/ndvi.py`:**
  - el comentario de las cajas ya no dice que todas son del Lab 3;
  - `enviar`, `consultar` y `bajar` aceptan zonas, archivo de tarea y carpeta, para reutilizarlos;
  - el docstring explica cómo se reproduce el JSON: hoy `enviar` pide las 3 zonas;
  - la autoprueba revisa las 3 zonas, las cajas, el aviso de Olmos y que las descartadas suban el q.
- **`lab3_olmos.py`:** ya no duplica código; usa `ndvi.enviar/consultar/bajar` con la zona de `ndvi.ZONAS`. `scripts/data/`, donde queda el task, ya estaba en `pipeline/exploracion/favio/.gitignore`.
- **`tests/api.rs`:** cita las fuentes reales (tareas `44445de3` y `ee736bc9`). Ya no exige `real` en Olmos, que puede cambiar con un año más, pero sí que lleve su aviso.
- **`tests/checks_ndvi.sh` + `test_ndvi_checks.py`:** las 3 zonas con id único y lat/lon dentro de su recuadro, con 3 roturas nuevas (10 en total).
- **`docs/vegetacion.md`:** las 6 zonas exploradas más Olmos; Olmos sale de «sin dato»; las tareas y el orden de las decisiones; el tamaño de la caja; El Niño; y la revisión de 2021–2022.
- **2021 y 2022 con la misma área:** no es un desfase. Se revisó el NetCDF: los 12 meses de cada año están bien y son conjuntos de píxeles distintos (difieren en 42) con el mismo conteo, 341.

