<!-- Lee CONDITIONS.md antes de enviar. -->

## Qué cambia
<!-- Resumen en 1-3 líneas -->

## Por qué
<!-- Problema o necesidad -->

## Cómo probarlo
<!-- Comandos o pasos -->

## Checklist (ver [CONDITIONS.md](../CONDITIONS.md))
- [ ] Mi rama sale de `developer` y el PR apunta a `developer`
- [ ] `bash tests/e2e.sh` pasa
- [ ] Añadí `changelog/<rama>.md`
- [ ] Commits con prefijo (`feat:`, `fix:`, `ci:`, `docs:`, `chore:`)
- [ ] No hay `NaN`, secretos ni archivos descargados en el diff
- [ ] Si toqué `pipeline/`, regeneré y commiteé `data/*.json`
- [ ] Si cambié el formato de un JSON, avisé al equipo y actualicé `docs/`
