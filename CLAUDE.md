# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

API de solo lectura (Rust/Axum) + pipeline de datos (Python) · NASA Space Apps 2026 «Detective del Perú». Todo en español.

**Esta guía es solo un índice: la fuente de verdad está en los documentos enlazados. Léelos y no dupliques su contenido aquí.**

## Lee primero

| Documento | Para qué |
|---|---|
| [`CONDITIONS.md`](CONDITIONS.md) | Reglas obligatorias antes de abrir un PR (ramas, changelog, commits, CI, revisión) |
| [`docs/reglas-datos.md`](docs/reglas-datos.md) | Reglas de datos: años completos, sin NaN, una fuente por JSON, costa |
| [`docs/datos.md`](docs/datos.md) | Qué datos hay (POWER), variables, limpieza y límites |
| [`docs/tendencias.md`](docs/tendencias.md) | Método y campos de las tendencias (`stats`), semáforo y avisos |
| [`docs/vegetacion.md`](docs/vegetacion.md) | NDVI: qué se confirmó y qué zonas no se usan |
| [`docs/guia-pipeline.md`](docs/guia-pipeline.md) | Cómo añadir una fuente nueva al pipeline y credenciales Earthdata |
| [`README.md`](README.md) | Estructura, uso y endpoints |
| `changelog/` | Un archivo por rama con lo que cambió |

## Comandos

```bash
bash tests/e2e.sh                    # valida datos + cargo test + prueba la API (es el CI; requiere jq)
cargo test cors                      # un test por nombre (tests/api.rs)
cargo run                            # API en :3000 (PORT, CORS_ORIGINS)
python pipeline/power.py 2001 2024   # regenera data/power.json (gpm.py: igual, con Earthdata)
python pipeline/tendencias.py        # regenera data/variables.json y data/zonas/ (los sirve /api/zonas)
```

## Lo esencial de la arquitectura

- `pipeline/` (Python) escribe `data/*.json`; `src/` (Rust) los sirve. Solo comparten esos JSON y la API **nunca calcula en vivo**.
- `data/power.json`, `data/gpm.json`, `data/variables.json`, `data/zonas/{lluvia,temperatura,lluvia_imerg}.json` y `data/ndvi.json` (lo sirve `/api/vegetacion`) se embeben con `include_str!` **al compilar**: cambiar datos exige recompilar. Un JSON inválido (p. ej. `NaN`) o que no cuadre entre archivos impide que la API arranque (`src/data.rs`): tras regenerar `power.json`/`gpm.json`, corre también `python pipeline/tendencias.py`.
- Endpoint nuevo = handler en `src/routes/` + modelo en `src/models/` + test en `tests/api.rs`.
- Flujo: PR a `developer` (nunca directo a `main`), rama `tipo/descripcion`, `changelog/<rama>.md`, CI `e2e` en verde (regla de equipo: GitHub no lo bloquea).
- Secretos solo en `.env` local (plantilla `.env.example`) o *secrets* de GitHub; nunca en el repo.
