# chore/env-ejemplo

- Añade `.env.example` (plantilla de `EARTHDATA_USERNAME` / `EARTHDATA_PASSWORD`).
- `docs/guia-pipeline.md`: paso `cp .env.example .env`.
- En GitHub Actions las mismas variables van como *secrets* del repo (no usan `.env`).
