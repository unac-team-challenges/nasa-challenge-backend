# nasa-challenge-backend

Detective del Perú · NASA Space Apps Challenge 2026 (equipo NASA-CHALLENGE-UNAC).

Pipeline de datos (Python) y API de solo lectura (Rust/Axum) que sirve los JSON ya procesados. Los datos se calculan antes; **la API nunca calcula en vivo**.

## Estructura
| Ruta | Qué es |
|---|---|
| `pipeline/` | Scripts Python: `power.py` (NASA POWER), `gpm.py` (GPM IMERG), `departamentos.py` (máscara de los 25 departamentos) y `tendencias.py` (Mann-Kendall, Sen, Benjamini-Hochberg). Escriben `data/`. `exploracion/` guarda los laboratorios del equipo |
| `data/` | JSON ya procesados: `power.json` y `gpm.json` (promedio anual por departamento) y las tendencias (`variables.json`, `zonas/`) que escribe `pipeline/tendencias.py` |
| `src/` | API Axum: `main.rs` (arranque), `lib.rs` (router + CORS), `config.rs`, `data.rs` (carga e índice), `models/` (forma de los JSON), `schema.rs` (respuestas), `routes/`, `error.rs`. Embebe `data/power.json` y `data/gpm.json` al compilar |
| `tests/` | `api.rs` (integración, `cargo test`) y `e2e.sh` (todo junto) |
| `docs/` | [`reglas-datos.md`](docs/reglas-datos.md) (reglas y fuentes elegidas) · [`datos.md`](docs/datos.md) (POWER y sus límites) · [`guia-pipeline.md`](docs/guia-pipeline.md) (cómo añadir una fuente) · [`tendencias.md`](docs/tendencias.md) (método de las tendencias) · [`vegetacion.md`](docs/vegetacion.md) (NDVI) |
| `changelog/` | Un archivo por rama con sus cambios |
| `CONDITIONS.md` | **Reglas obligatorias antes de abrir un PR** |

## Uso
```bash
pip install -r pipeline/requirements.txt
python pipeline/power.py 2001 2024   # regenera data/power.json
python pipeline/gpm.py 2001 2024     # regenera data/gpm.json (necesita .env con Earthdata)
python pipeline/tendencias.py        # regenera variables.json y zonas/ desde power.json y gpm.json
cargo run                            # http://0.0.0.0:3000 (PORT para cambiarlo)
bash tests/e2e.sh                    # verifica que todo corre
```

**Dependencias de Python.** `pipeline/requirements.txt` lista solo las directas (versiones fijas). `pipeline/requirements.lock` fija **todas**, con hashes, para Python 3.12 en Linux; es lo que instalan el CI y el cron (`pip install --require-hashes -r pipeline/requirements.lock`). Si cambias `requirements.txt` (o dependabot lo cambia), regenera el lock:
```bash
pip install uv
uv pip compile pipeline/requirements.txt --python-version 3.12 --python-platform linux --generate-hashes -o pipeline/requirements.lock
```

| Endpoint | Respuesta |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /regiones` | Lista de regiones con lat/lon |
| `GET /api/variables` | Variables del producto (`lluvia`, `temperatura`) con unidad, fuente y rango de años (`data/variables.json`) |
| `GET /api/zonas?variable=` | Las 25 zonas con ubigeo como texto (`"01"`–`"25"`), `celdas`, `nota?` y `stats` (tendencia y semáforo `status`), sin series. `variable` obligatoria (400 si falta o no existe) |
| `GET /api/openapi.json` | Contrato OpenAPI (también en `openapi.json`; se regenera con `UPDATE_OPENAPI=1 cargo test openapi`) |
| `GET /api/zonas/{id}?variable=` | Serie anual de la zona (`serie: [{anio, valor}]`) y su `stats` del mismo periodo (`aviso` siempre en lluvia); 404 si el ubigeo no existe |
| `GET /api/vegetacion` | Vegetación del Caso 2 (`data/ndvi.json`, MODIS MOD13A3): Chavimochic e Ica-Villacurí, cada una con `unidad_geografica` (recuadro sobre el valle, **no** el departamento), `serie: [{anio, ndvi_anual, area_verde_km2}]` y `stats` con su `status` |
| `GET /gpm/{region}` | Lluvia anual GPM IMERG de la región (`lluvia_mm_dia` por año; mismas reglas de búsqueda y 404 que `/power`) |
| `GET /power/{region}` | Promedios anuales de la región (404 JSON si no existe; ignora mayúsculas y tildes: `/power/ancash`) |

CORS: siempre `localhost`/`127.0.0.1`. Para añadir la URL de Vercel: variable de entorno `CORS_ORIGINS=https://tu-app.vercel.app` (varias separadas por coma, sin `/` final).

## Despliegue (Render)
`render.yaml` define el servicio web (Rust, `cargo build --release` / `cargo run --release`, health check en `/health`). Pasos: Render → **New → Blueprint** → elegir este repo → rellenar `CORS_ORIGINS` con la URL de Vercel. Render inyecta `PORT` y la API ya escucha en `0.0.0.0:$PORT`. Cada push a la rama desplegada redespliega solo; si el build falla, sigue la versión anterior. Los datos van embebidos en el binario, así que no hay disco ni base de datos.

## Ramas
- `developer`: aquí se integra todo (vista previa en Vercel).
- `main`: solo lo que ya funciona (producción). Se actualiza únicamente con PR desde `developer`.

Antes de escribir un PR, lee [`CONDITIONS.md`](CONDITIONS.md).
