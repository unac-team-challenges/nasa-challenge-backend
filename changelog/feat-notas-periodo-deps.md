# feat/notas-periodo-deps

PR apilado sobre #22 (`feat/pipeline-promedio-departamento`) → cuando la #22 entre, se retargetea a `developer`.

## Cambiado
- **Periodo de POWER: 2001–2024** (antes 1981–2024), igual que GPM. `power.py`, el workflow mensual, README, CLAUDE.md y docs. `data/power.json` regenerado (mismos valores que la corrida de 1981, solo sin los años anteriores a 2001).
- `pipeline/requirements.txt`: **versiones fijas** (`==`), las probadas; resuelven en Python 3.12 (el del workflow). Dependabot (ya configurado) abre el PR para subirlas.
- `docs/tendencias.md`: guía para Josue (pendiente de Sen, Mann-Kendall, `stats`) con el estado actual: promedio del departamento ya implementado, periodo 2001–2024, `celdas`/`nota`, reparto con la API.

## Añadido
- `GET /api/zonas/{id}?variable=` devuelve `nota` cuando el promedio de esa variable es poco fiable (menos de 4 celdas); la nota sale de la fuente de la variable (lluvia → GPM, temperatura → POWER). `openapi.json` actualizado.
- Test `zona_devuelve_la_nota_de_su_variable` y comprobación en `tests/e2e.sh`.
