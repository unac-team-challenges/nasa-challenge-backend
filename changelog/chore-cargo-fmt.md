# chore/cargo-fmt

PR: base `developer`.

## Cambiado
- `cargo fmt` sobre todo el código Rust (`src/`, `tests/`). Solo formato: ningún cambio de comportamiento.
- `ci.yml`: el CI corre `cargo fmt --check` y `cargo clippy --all-targets -- -D warnings` antes de `tests/e2e.sh`. Un PR sin formatear ya no pasa.

## Notas
- `cargo clippy -D warnings` ya salía limpio en `developer`.
- No hay ramas abiertas que toquen Rust (#42 solo toca Python, datos y docs), así que no debería haber conflictos.
- Antes de abrir un PR: `cargo fmt`. Lo avisa también `bash tests/verificar.sh`.
