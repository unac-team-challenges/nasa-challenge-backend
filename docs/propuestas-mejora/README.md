# Propuestas de mejora pendientes del backend

Estado al 2026-11-14. Lo que ya se aplicó (404 JSON, `Cache-Control`, apagado ordenado, `deny_unknown_fields`, rangos físicos en `e2e`, versiones fijas en `requirements.txt`, `permissions`/`concurrency`/dependabot en el CI, Callao, despliegue en Render) **se quitó de estos documentos**; su historia está en `changelog/`.

Este documento **no cambia código**: cada punto dice **por qué** importa y **cómo** se arreglaría. Ninguno es obligatorio.

## Pendientes

| # | Hallazgo | Severidad | Esfuerzo | Documento |
|---|---|---|---|---|
| 1 | El cron mensual nunca se ha ejecutado (falta lanzarlo una vez a mano) | Alta | 5 min | [03 §1](03-ci-cd-y-repo.md#1-el-cron-de-datos-nunca-se-ejecuta) |
| 2 | El bot sube datos a `developer` sin pasar por `e2e` | Alta | 15 min | [03 §2](03-ci-cd-y-repo.md#2-el-bot-sube-datos-sin-validarlos) |
| 3 | IMERG V07 terminó en 2025-09: 2025 nunca será año completo | Alta | Decisión | [02 §1](02-pipeline-y-datos.md#1-imerg-v07-ya-no-se-actualiza) |
| 4 | IMERG V07 mensual empieza en 1998-01, no en 2001 | Media | 10 min | [02 §2](02-pipeline-y-datos.md#2-imerg-empieza-en-1998-no-en-2000) |
| 5 | `power.py` no reintenta | Media | 15 min | [02 §4](02-pipeline-y-datos.md#4-powerpy-no-reintenta) |
| 6 | Años descartados sin aviso | Media | 15 min | [02 §5](02-pipeline-y-datos.md#5-años-descartados-sin-aviso) |
| 7 | `cargo fmt --check` y `clippy -D warnings` en CI | Media | 30 min | [03 §4](03-ci-cd-y-repo.md#4-ci-lo-que-falta-y-cuesta-poco) |
| 8 | Primer `developer → main` | Media | Decisión | [03 §7](03-ci-cd-y-repo.md#7-main-como-producción) |
| 9 | Flujo «static-first» con espejo generado desde la API | Propuesta | 1-2 h | [04](04-flujos-y-tecnologias.md) |

Menores de la API que siguen sin hacerse: edición Rust 2024, `rust-toolchain.toml`, `utoipa` 6 y logs de peticiones (`tracing`).

**Severidad:** *Alta* = puede romper la demo o dejar datos malos sin aviso. *Media* = afecta calidad o costo. *Baja* = pulido.

## Documentos

1. [`02-pipeline-y-datos.md`](02-pipeline-y-datos.md): scripts Python y los JSON.
2. [`03-ci-cd-y-repo.md`](03-ci-cd-y-repo.md): GitHub Actions y flujo del repo.
3. [`04-flujos-y-tecnologias.md`](04-flujos-y-tecnologias.md): proyectos parecidos, tecnologías actuales y un flujo propuesto.
