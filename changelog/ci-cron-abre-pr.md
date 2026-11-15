# ci/cron-abre-pr

PR: base `developer`.

## Cambiado
- `actualizar-datos.yml` ya no hace `git push` a `developer`. Corre `bash tests/e2e.sh` en el mismo job y, solo si pasa y `data/` cambió, sube la rama `datos/actualizacion-AAAA-MM-DD` y abre un PR a `developer`. Una persona ve el diff de `data/` antes de mezclar.
- Permisos del workflow: `pull-requests: write`. `timeout-minutes: 90` (antes 360) y `concurrency: actualizar-datos` (un solo cron a la vez).

## Por qué
Un push (o un PR) hecho con el `GITHUB_TOKEN` no dispara otros workflows: el commit del bot nunca pasaba por el `e2e` del CI. Ahora el `e2e` corre dentro del job, antes de proponer nada.

## Pendiente (quien administra el repo)
- Activar **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. Hoy está desactivado (`can_approve_pull_request_reviews: false`). Sin eso el job sube la rama, avisa con un `warning` y el PR se abre a mano desde el enlace de GitHub.
- Lanzar el workflow una vez a mano (`workflow_dispatch`) para comprobarlo: nunca se ha ejecutado.

## Notas
- El PR del bot tampoco dispara el CI por el mismo motivo: por eso el `e2e` corre en el job. El PR no lleva `changelog/` (es automático).
- No se tocaron las líneas de `pip install` para no chocar con #47 (lockfile de Python).
