# fix/cobertura-revision

PR: base `developer`. Autor: Favio. Pendientes que dejó Leandro al mezclar el #55.

## Corregido (`pipeline/cobertura.py`)
- **El área salía ~0,7 % alta:** `km2_pixeles` usaba 111,32 km por grado también para la latitud, y cerca del ecuador un grado de latitud mide ~110,6 km. Ahora `km_por_grado()` usa el largo real de cada grado en el elipsoide WGS84. La autoprueba ya no se compara con la misma fórmula: usa una independiente (la zona esférica con el radio de igual área de la Tierra) y comprueba los valores del ecuador (110,57 y 111,32 km).
- **`bajar()` sin `.nc`:** si el bundle no trae ningún `.nc`, ahora se detiene con un mensaje y no toca la caché. Antes borraba la copia buena.
- **`.part` huérfano:** si la descarga falla a mitad de un archivo, también se borra ese `.part` (antes solo se limpiaban los ya terminados).
- `data/cobertura_arboles.json` regenerado. La tendencia no cambia (Sen e IC iguales):
  - **La Pampa:** bosque de 729 → 464 a **724 → 462 km²** (−36 %);
  - **Iquitos:** 491 km², igual al tamaño de su recuadro.
- **`bajar()`:** al empezar borra los `.part` que dejó una corrida anterior que murió sin limpiar (p. ej. `kill -9`).

## Otros
- `tests/e2e.sh`: los checks de `cobertura.py` usan `$PY` (la `.venv` si existe), como los de `ndvi.py`.
- `docs/vegetacion.md`: cifras al día y cómo se calcula el área.
- `changelog/feat-cobertura-arboles.md`: decía que #56 (Olmos) ya había entrado al mezclar #55, y no era así.

## Pendiente (se deja para otro PR)
- Extraer un `appeears.py` común con `ndvi.py` y simplificar el trait `Recuadro` a un `ZonaRecuadro<A>` genérico (revisión de #55, opcional).
- Decisión de La Pampa (`posible_casualidad` por lag1) y frontend (`pnpm gen`, dónde se muestra la selva).
