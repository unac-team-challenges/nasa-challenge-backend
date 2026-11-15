# chore/lockfile-python

PR: base `developer`.

## Añadido
- `pipeline/requirements.lock`: las 57 dependencias de Python (directas e indirectas) con versión exacta y hashes, generado con `uv pip compile` para Python 3.12 en Linux. Comprobado con `uv pip install --dry-run --require-hashes`.

## Cambiado
- `ci.yml` y `actualizar-datos.yml` instalan con `pip install --require-hashes -r pipeline/requirements.lock` y cachean por ese archivo. El CI y el cron usan siempre las mismas versiones.
- `README.md`: cómo regenerar el lock.

## Notas
- `requirements.txt` sigue siendo la lista de dependencias directas y lo que se usa en local. Dependabot sigue actualizando `requirements.txt`; al mezclar uno de sus PR hay que regenerar el lock (comando en el `README`).
- El lock es solo para Linux y Python 3.12 (el del CI). En otra plataforma, `requirements.txt`.
