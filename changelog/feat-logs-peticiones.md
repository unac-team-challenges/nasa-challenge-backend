# feat/logs-peticiones

Logs de peticiones con `tracing` (pendiente de `docs/propuestas-mejora/README.md`).

## Añadido
- `src/lib.rs`: `TraceLayer` de `tower-http` (feature `trace`), a nivel INFO: método, ruta, estado y latencia de cada petición.
- `src/main.rs`: `tracing_subscriber` con filtro por `RUST_LOG` (por defecto `info`); el aviso de arranque pasa de `println!` a `tracing::info!`.
- Dependencias nuevas: `tracing` 0.1 y `tracing-subscriber` 0.3 (feature `env-filter`).
- `README.md`: una línea sobre `RUST_LOG`.

## Notas
- El router de los tests (`app()`) no inicia ningún suscriptor, así que `cargo test` no imprime logs.
- La ruta se registra con su query (`?variable=...`); no hay datos personales en la API.
- `docs/propuestas-mejora/README.md` ya no lista «logs de peticiones» entre los pendientes (era el último menor de la API).
