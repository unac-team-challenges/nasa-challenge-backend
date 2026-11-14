# nasa-challenge-backend

Detective del Perú · NASA Space Apps Challenge 2026 (equipo NASA-CHALLENGE-UNAC).

Pipeline de datos (Python) y API de solo lectura (Rust/Axum) que sirve los JSON ya procesados. Los datos se calculan antes; **la API nunca calcula en vivo**.

## Estructura
| Ruta | Qué es |
|---|---|
| `pipeline/` | Scripts Python que descargan datos de NASA y escriben `data/*.json` |
| `data/` | JSON ya procesados (promedio anual por región) |
| `src/` | API Axum: `main.rs` (arranque), `lib.rs` (router + CORS), `config.rs`, `data.rs` (carga e índice), `models/` (forma de los JSON), `schema.rs` (respuestas), `routes/`, `error.rs`. Embebe `data/power.json` y `data/gpm.json` al compilar |
| `tests/` | `api.rs` (integración, `cargo test`) y `e2e.sh` (todo junto) |
| `docs/` | [`datos.md`](docs/datos.md) (qué datos hay y sus límites) · [`guia-pipeline.md`](docs/guia-pipeline.md) (cómo añadir una fuente) |
| `changelog/` | Un archivo por rama con sus cambios |
| `CONDITIONS.md` | **Reglas obligatorias antes de abrir un PR** |

## Uso
```bash
pip install -r pipeline/requirements.txt
python pipeline/power.py 2001 2024   # regenera data/power.json
cargo run                            # http://0.0.0.0:3000 (PORT para cambiarlo)
bash tests/e2e.sh                    # verifica que todo corre
```

| Endpoint | Respuesta |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /regiones` | Lista de regiones con lat/lon |
| `GET /api/variables` | Variables del producto (`lluvia`, `temperatura`) con unidad, fuente y rango de años |
| `GET /api/zonas?variable=` | Las 25 zonas con ubigeo como texto (`"01"`–`"25"`), sin series. `variable` obligatoria (400 si falta o no existe) |
| `GET /api/openapi.json` | Contrato OpenAPI (también en `openapi.json`; se regenera con `UPDATE_OPENAPI=1 cargo test openapi`) |
| `GET /api/zonas/{id}?variable=` | Serie anual de la zona (`serie: [{anio, valor}]`); 404 si el ubigeo no existe. Los campos de tendencia (`stats`) llegan con el cálculo de Sebastian |
| `GET /gpm/{region}` | Lluvia anual GPM IMERG de la región (`lluvia_mm_dia` por año; mismas reglas de búsqueda y 404 que `/power`) |
| `GET /power/{region}` | Promedios anuales de la región (404 JSON si no existe; ignora mayúsculas y tildes: `/power/ancash`) |

CORS: siempre `localhost`/`127.0.0.1`. Para añadir la URL de Vercel: variable de entorno `CORS_ORIGINS=https://tu-app.vercel.app` (varias separadas por coma, sin `/` final).

## Ramas
- `developer`: aquí se integra todo (vista previa en Vercel).
- `main`: solo lo que ya funciona (producción). Se actualiza únicamente con PR desde `developer`.

Antes de escribir un PR, lee [`CONDITIONS.md`](CONDITIONS.md).
