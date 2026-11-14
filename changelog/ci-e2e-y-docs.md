# ci/e2e-y-docs

PR: base `ci/actualizar-datos` (#6); pasa a `developer` cuando #6 se mezcle.

## Añadido
- `tests/e2e.sh`: valida `data/power.json`, compila, levanta la API y prueba endpoints, 404, acentos y CORS.
- `.github/workflows/ci.yml`: corre el e2e en cada PR y push a `developer`/`main`.
- `CONDITIONS.md`: reglas obligatorias antes de abrir un PR.
- `.github/pull_request_template.md`: checklist que enlaza a `CONDITIONS.md`.
- `docs/datos.md` y `docs/guia-pipeline.md`: guías movidas al repo y actualizadas (sin `NaN`, solo años completos).

## Cambiado
- `README.md` reescrito con estructura, uso y enlaces a `docs/` y `CONDITIONS.md`.

## Notas
- Sin protección de ramas: el repo es privado en plan free y GitHub no la ofrece. Se cumple como regla de equipo (ver `CONDITIONS.md`).
