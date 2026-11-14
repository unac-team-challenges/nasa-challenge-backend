# nasa-challenge-backend

Detective del Perú · NASA Space Apps Challenge 2026 (equipo NASA-CHALLENGE-UNAC).

Pipeline de datos (Python) y API de solo lectura (Rust/Axum) que sirve los JSON ya procesados. Los datos se calculan antes; **la API nunca calcula en vivo**.

## Estructura
| Ruta | Qué es |
|---|---|
| `pipeline/` | Scripts Python que descargan datos de NASA y escriben `data/*.json` |
| `data/` | JSON ya procesados (promedio anual por región) |
| `src/main.rs` | API Axum; embebe `data/power.json` al compilar |
| `tests/e2e.sh` | Prueba e2e: compila, levanta la API y verifica endpoints |
| `docs/` | [`datos.md`](docs/datos.md) (qué datos hay y sus límites) · [`guia-pipeline.md`](docs/guia-pipeline.md) (cómo añadir una fuente) |
| `changelog/` | Un archivo por rama con sus cambios |
| `CONDITIONS.md` | **Reglas obligatorias antes de abrir un PR** |

## Uso
```bash
pip install -r pipeline/requirements.txt
python pipeline/power.py 2015 2020   # regenera data/power.json
cargo run                            # http://0.0.0.0:3000 (PORT para cambiarlo)
bash tests/e2e.sh                    # verifica que todo corre
```

| Endpoint | Respuesta |
|---|---|
| `GET /regiones` | Lista de regiones con lat/lon |
| `GET /power/{region}` | Promedios anuales de la región (404 si no existe) |

CORS: solo `localhost`/`127.0.0.1`. Añadir la URL de Vercel en `origen_permitido` (`src/main.rs`).

## Ramas
- `developer`: aquí se integra todo (vista previa en Vercel).
- `main`: solo lo que ya funciona (producción). Se actualiza únicamente con PR desde `developer`.

Antes de escribir un PR, lee [`CONDITIONS.md`](CONDITIONS.md).
