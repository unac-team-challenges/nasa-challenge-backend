# feat/cobertura-arboles

PR: base `developer` (#42 y #50 ya mezclados; reutiliza el modelo de recuadros de #50 y su `serie` como lista). Autor: Favio. Es la parte 2 de la tarea de vegetación (selva).

## Añadido
- **`pipeline/cobertura.py`**: cobertura de árboles de **MODIS MOD44B v061** (250 m, anual) vía AppEEARS, con la misma estructura que `ndvi.py` (`enviar`, `estado`, `bajar`, `calcular`, `autoprueba`). Reutiliza la sesión de AppEEARS de `ndvi.py` y `clasificar()` de `tendencias.py`, sin copiar los umbrales. Bosque = 30 % o más de árboles.
- **`data/cobertura_arboles.json`** (tarea AppEEARS `47c3f635…`):
  - **La Pampa** (Madre de Dios, minería de oro): árboles de 74,1 % a 45,9 % y bosque de 729 a 464 km² (−36 %). Sen −15,3 puntos por década, IC [−17,5; −12,5], q < 0,001. Pero **lag1 = 0,58**, así que queda `posible_casualidad` con su aviso.
  - **Iquitos** (contraste): de 76,7 % a 79,7 %, +1,3 puntos por década con p = 0,064 e IC [−0,2; +2,9], es decir, **no distinguible de 0**. El área de bosque queda en el tope (casi todo el recuadro), así que el contraste es la tendencia, no los km².
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
- Frontend: `pnpm gen` y decidir dónde se muestra la selva (¿ficha de Madre de Dios y Loreto, como el Caso 2?).

## Ajustes tras la revisión de Leandro
- **Actualizado con `developer`** (ya entró #53, la lluvia de POWER con `lluvia_imerg`; #56, Olmos, seguía abierto al mezclar este PR). Se resolvió el conflicto de `CLAUDE.md`, con la coma que faltaba en la lista de archivos embebidos.
- **`pipeline/cobertura.py`:**
  - el área de bosque ya no usa un píxel constante: se calcula por fila de latitud (× cos(lat), con `km2_pixeles()`), porque el ráster está en grados. Antes salía inflada: Iquitos tenía más bosque que área de recuadro. La Pampa pasa de 746 → 475 a **729 → 464 km²**, con la misma caída de −36 %;
  - con menos de 3 años, `zona_json` falla con el motivo, en vez de escribir un `stats` incompleto que haría caer la API. La autoprueba cubre 0 y 2 años y comprueba que todos los `status` tengan el esquema completo de `Stats`;
  - los años se leen con `ds["time"].dt.year`, que sirve con datetime64 y con cftime, como en `ndvi.py`;
  - un año con huecos (fracción con dato de 0,5 o más) extrapola el bosque a toda la tierra según la fracción con dato por área (`resumen_anio()`), así que no hay escalones falsos en los km². Está probado en la autoprueba;
  - `bajar()` descarga a archivos `.part` y solo reemplaza los `.nc` cuando todo bajó: si la descarga se corta, la copia buena sigue.
- **Textos:** Iquitos pasa de «estable» a «no distinguible de 0», y se aclara que su área está en el tope del recuadro.
- `data/cobertura_arboles.json` regenerado. La tendencia (Sen e IC) no cambia; solo cambian los km².
- **No se hizo (opcional, según la revisión):** extraer un `appeears.py` común con `ndvi.py` y simplificar el trait `Recuadro` a un `ZonaRecuadro<A>` genérico. Quedan para otro PR.

