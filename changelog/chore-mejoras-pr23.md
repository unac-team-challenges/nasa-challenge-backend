# chore/mejoras-pr23

Aplica las propuestas de `docs/propuestas-mejora/` (PR #23) que no tocan el pipeline ni el workflow del cron (esos archivos los cambia #22; van en otra PR cuando #22 se mezcle).

## API (01)
- Cualquier ruta inexistente (`/noexiste`, `/power/lima/`) responde 404 **JSON** (`fallback`).
- `Cache-Control: public, max-age=3600, s-maxage=86400` en los datos; `/health` va con `no-store`. Feature `set-header` de `tower-http`.
- Apagado ordenado con Ctrl+C y SIGTERM (feature `signal` de tokio); mensajes de arranque correctos (`data/*.json`, puerto).
- `deny_unknown_fields` en `Region<M>` y en las medidas: un campo de más en el JSON hace fallar el arranque.
- `Datos::desde_json` falla si `power.json` y `gpm.json` no tienen las mismas regiones.
- Los errores recortan a 60 caracteres lo que reflejan del usuario.
- 3 tests nuevos en `tests/api.rs` (18 en total).

## Validación (02, 03)
- `tests/e2e.sh`: rangos físicos (lluvia 0–30 mm/día, `T2M` −15–35 °C) y comprobaciones del 404 JSON y del `Cache-Control`.
- `ci.yml`: `permissions: contents: read` y `concurrency` con `cancel-in-progress`.
- `.github/dependabot.yml` (mensual: cargo, pip, actions).

## Docs
- `docs/reglas-datos.md` y `docs/tendencias.md`: IMERG v07 existe de ene 1998 a sep 2025 (verificado en CMR); 2025 nunca será año completo; no mezclar con otra versión ni con Early/Late.

## No incluido (decisión del equipo o toca archivos de #22)
- Cron: cambiar la rama por defecto/primer `developer → main`, quitar `gpm.py` del cron (IMERG congelado), correr `e2e` antes del commit del bot, `timeout`/`concurrency` del job, reintentos en `power.py`, avisos de años descartados, versiones fijas en `requirements.txt`, regenerar `gpm.json` desde 1998.
- `cargo fmt --check` y `clippy -D warnings` en CI: no hay `rustfmt`/`clippy` instalados en la máquina de desarrollo para formatear antes.
- Despliegue (Vercel estático / contenedor), `utoipa` 6, edición 2024, compresión y logs con `tracing`.
