# feat/ndvi-olmos

PR: base `developer`. Autor: Favio. Es la parte 2 de la tarea de vegetación (Olmos).

## Añadido
- **Olmos** es la tercera zona de `data/ndvi.json` y de `/api/vegetacion`, con el recuadro movido a las tierras nuevas del proyecto: (−80,15, −6,25, −79,90, −6,00).
  - Es la caja de 0,25° con más campos de cultivo en OpenStreetMap (unos 4.400 frente a unos 150 en la caja vieja). **Se eligió sin mirar el NDVI.**
  - NDVI de 0,224 a 0,331; Sen +0,081 por década, IC [0,025; 0,129], **real**.
  - Área verde media: de **35 km²** (2001–2013) a **341 km²** (2016–2024). El salto empieza en 2016–2017, con la llegada del agua.
- `pipeline/exploracion/favio/scripts/lab3_olmos.py`: la solicitud a AppEEARS (tarea `ee736bc9…`).

## Cambiado
- `pipeline/ndvi.py`: Olmos en `ZONAS` y la documentación de las zonas al día.
- `data/ndvi.json` regenerado. Chavimochic e Ica no cambian; con 3 zonas, Benjamini-Hochberg sigue dándolas reales.
- `tests/api.rs`: el test de `/api/vegetacion` revisa las 3 zonas con sus cifras de 2001 y 2024.
- `docs/vegetacion.md`: Olmos pasa de «sin dato» a resuelto, con el detalle y el cuidado con los años de El Niño.

## Pendiente
- Frontend: mostrar Olmos en el Caso 2 (ficha de Lambayeque) desde `/api/vegetacion`.
