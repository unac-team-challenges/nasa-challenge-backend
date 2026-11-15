# docs/propuestas-al-dia

Pone al día `docs/propuestas-mejora/` (verificado el 2026-11-15). Solo docs; no cambia código, workflows ni `data/`.

## Quitado (ya está hecho)
- Propuesta 1, cron nunca ejecutado: corrió bien por `workflow_dispatch` (run 43673698147). Secrets `EARTHDATA_*` y «Allow Actions to create PRs» activos.
- Propuesta 2, el bot sube datos sin `e2e`: `actualizar-datos.yml` corre `bash tests/e2e.sh` y abre un PR.
- Propuesta 3, IMERG V07 termina en 2025-09: `gpm.py` es incremental y `docs/reglas-datos.md` dice que 2025 nunca será año completo.
- Propuesta 4, IMERG desde 1998: decidido, se queda en 2001–2024.
- Propuesta 5, `power.py` sin reintentos: `SESION` con `Retry` en `power.py`.
- Propuesta 6, años descartados sin aviso: `gpm.py` imprime `AVISO` en stderr.
- Propuesta 7, `fmt` y `clippy` en CI: ya están en `ci.yml`.
- Propuesta 8, primer `developer → main`: `origin/main` y `origin/developer` no difieren.

Quitados del `README` de la carpeta: filas 1 a 8 de «Pendientes». La 9 (static-first) queda como 1, con la línea «Aplicado el 2026-11-15».

Secciones borradas:
- `02-pipeline-y-datos.md` §4 (`power.py` no reintenta) y §5 (años descartados sin aviso).
- `03-ci-cd-y-repo.md` §1 (el cron nunca se ejecuta) y §7 (`main` como producción).
- En `02` §1, el enlace a `03` §1 (borrada) se quitó y quedó solo el texto.

## Conservado a propósito
Son secciones con algo que todavía vale y que no está en la tabla. Según la regla de la tarea se dejan y se anotan:
- `02` §1 (IMERG V07 ya no se actualiza): la regla «no rellenar 2025 con IMERG Late/Early» y la de «V08 no se mezcla con V07» no están en la tabla.
- `02` §2 (IMERG empieza en 1998): la advertencia de TRMM antes de 2014 (revisar saltos de homogeneidad en V07) no está en la tabla.
- `03` §2 (el bot sube datos sin validarlos): el texto «Qué pasa» describe el `git push` directo, que ya no existe. Lo que sigue vigente es que el bot abre PR con `GITHUB_TOKEN`, que no dispara CI; hace falta GitHub App o PAT para eso. Está sin tabla.
- `03` §4 (CI: lo que falta): `cargo-deny` (opcional) no está en la tabla; `fmt` y `clippy` sí están hechos.

## Pendiente que no se perdió
- Quitar `-W ignore` de `actualizar-datos.yml` (propuesta 6). Hacerlo solo después de lanzar el workflow, como dice la tabla anterior.
- `03` §5 dice «Ayuda también con el punto 6». El «punto 6» ya no existe en el `README`; revisar si la frase sigue teniendo sentido.
