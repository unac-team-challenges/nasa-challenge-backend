# chore/verificacion-corta

PR: base `developer`. Separado de `feat/pipeline-ndvi` (#42) para cumplir «un PR = un tema».

## Añadido
- `tests/verificar.sh`: compila y autoprueba los scripts de Python, `cargo clippy -D warnings` y el e2e. Imprime una línea por paso y, si algo falla, solo las líneas útiles; el log completo queda en `/tmp/verificar-<rama>.log`. `bash tests/verificar.sh rapido` omite el e2e. Si existe `.venv/`, la usa, como hace el CI con sus dependencias.
- `.claude/agents/verificador.md` (modelo haiku): corre `verificar.sh` y resume los fallos con su arreglo.
- `.claude/agents/revisor-datos.md` (modelo sonnet): revisa `pipeline/` y `data/` contra `docs/reglas-datos.md` y `docs/tendencias.md`, sin copiar sus umbrales.

## Notas
- `cargo fmt --check` sale como aviso, no como fallo: `developer` aún no está formateado y el CI no lo exige. Formatearlo es otro PR.
- No cambia el CI ni el código de la API ni del pipeline.
