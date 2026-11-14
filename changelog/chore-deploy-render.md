# chore/deploy-render

## Añadido
- `render.yaml` (Blueprint de Render): servicio web Rust, plan free, build `cargo build --release`, start `cargo run --release`, health check `/health`.
- Sección «Despliegue (Render)» en `README.md`.

## Notas
- Sin cambios de código: la API ya lee `PORT` y escucha en `0.0.0.0`.
- La guía oficial usa Rocket; este proyecto usa Axum. Los pasos de Render (build/start) son idénticos.
- Pendiente (manual, cuenta de Render): crear el Blueprint y definir `CORS_ORIGINS` con la URL de Vercel.
