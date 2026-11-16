# chore/edicion-rust-2024

Pasa el crate a la edición Rust 2024 (pendiente de `docs/propuestas-mejora/README.md`).

## Cambiado
- `Cargo.toml`: `edition = "2024"` (la toolchain ya está fijada en 1.99.0).
- `cargo fix --edition` no necesitó cambios de código. `cargo fmt` con el estilo 2024 solo reordena los `use` (y reajusta formato en `tests/api.rs`).
- Sin cambios de comportamiento: `tests/verificar.sh` da TODO OK.
