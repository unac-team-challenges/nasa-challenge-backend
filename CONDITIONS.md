# Condiciones para subir cambios

Léelo cada vez que abras un PR. La plantilla del PR te lo recuerda.

## Ramas
- `main`: producción. Solo recibe PR desde `developer`.
- `developer`: integración. Todo PR normal apunta aquí.
- Tu rama sale de `developer` y se llama `tipo/descripcion-corta`: `feat/`, `fix/`, `ci/`, `docs/`, `chore/`.

## Antes de abrir el PR
1. **`bash tests/e2e.sh` pasa** (incluye `cargo test`) en tu máquina. El CI lo corre igual y, si falla, el PR no se mezcla.
2. **Changelog**: crea `changelog/<rama>.md` (el `/` del nombre pasa a `-`: `feat/api-power` → `changelog/feat-api-power.md`) con lo añadido, corregido y pendiente.
3. **Commits** con prefijo: `feat:`, `fix:`, `ci:`, `docs:`, `chore:`.
4. Un PR = un tema. Si tocas dos cosas distintas, son dos PR.

## Reglas del proyecto
- **La API nunca calcula en vivo**: lo calculado vive en `data/*.json`, generado por `pipeline/`.
- **Contrato de datos**: no cambies la forma de los JSON sin avisar al equipo (ver [`docs/datos.md`](docs/datos.md) y [`docs/guia-pipeline.md`](docs/guia-pipeline.md)).
- **Nunca `NaN` en los JSON**: no es JSON válido y la API no arranca. El pipeline usa `allow_nan=False`.
- Si cambias `pipeline/`, regenera `data/` y commitea el JSON resultante.
- **No subir**: `.env`, credenciales, archivos descargados (`.hdf5`, `.nc4`, `.tif`), `target/`, `.venv/`.
- Secretos (Earthdata, etc.) solo como *secrets* de GitHub Actions.
- Orígenes CORS nuevos (p. ej. Vercel): variable `CORS_ORIGINS`, sin tocar código (ver `src/config.rs`).
- Endpoint nuevo: handler en `src/routes/`, modelo en `src/models/`, y un test en `tests/api.rs`.

## Revisión
- Al menos 1 aprobación de otra persona del equipo.
- CI en verde. GitHub no bloquea el merge (repo privado, plan free): **nadie mezcla con el check `e2e` en rojo**; es regla del equipo.
- Quien abre el PR responde los comentarios; quien revisa no mezcla su propio PR.
