# feat/cobertura-arboles

PR: base `feat/ndvi-api` (#50), porque reutiliza su modelo de recuadros. Autor: Favio. Es la parte 2 de la tarea de vegetación (selva).

## Añadido
- **`pipeline/cobertura.py`**: cobertura de árboles de **MODIS MOD44B v061** (250 m, anual) vía AppEEARS, con la misma estructura que `ndvi.py` (`enviar`, `estado`, `bajar`, `calcular`, `autoprueba`). Reutiliza la sesión de AppEEARS de `ndvi.py` y `clasificar()` de `tendencias.py`, sin copiar los umbrales. Bosque = 30 % o más de árboles.
- **`data/cobertura_arboles.json`** (tarea AppEEARS `47c3f635…`):
  - **La Pampa** (Madre de Dios, minería de oro): árboles de 74,1 % a 45,9 % y bosque de 746 a 475 km² (−36 %). Sen −15,3 puntos por década, IC [−17,5; −12,5], q < 0,001. Pero **lag1 = 0,58**, así que queda `posible_casualidad` con su aviso.
  - **Iquitos** (contraste): estable, de 76,7 % a 79,7 %, con un IC que incluye 0.
- **`GET /api/cobertura-arboles`** (`src/models/cobertura.rs`). La validación de recuadros de `data.rs` pasa a ser una sola para `ndvi.json` y `cobertura_arboles.json` (trait `Recuadro` + `recuadros()`).
- Tests:
  - el endpoint, con las cifras reales;
  - 8 roturas de `cobertura_arboles.json` que impiden arrancar;
  - el test de openapi ahora cubre las 5 rutas.
- e2e: compila `cobertura.py`, corre su autoprueba, pasa `tests/checks_cobertura.sh` y prueba `/api/vegetacion` y `/api/cobertura-arboles`.
- Docs: `README.md`, `CLAUDE.md` y `docs/vegetacion.md` (sección de la selva con resultados).

## Para decidir (equipo)
- **La Pampa no sale `real` por el lag1**, aunque la pérdida de bosque es grande y el IC no incluye 0. La serie es estable hasta 2009 y luego cae fuerte. No cambié el criterio único. Si se quiere tratar los quiebres de otra forma, es una decisión de `docs/tendencias.md`.

## Pendiente
- Mezclar después de #42 y #50.
- Frontend: `pnpm gen` y decidir dónde se muestra la selva (¿ficha de Madre de Dios y Loreto, como el Caso 2?).
