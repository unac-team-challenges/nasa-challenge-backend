# Propuestas de mejora del backend (rama `developer`)

**Fecha:** 2026-11-14 · **Base revisada:** `developer` @ `7fc8c70` y el PR abierto #21 (`feat/openapi-utoipa`) · **Para:** @leandro291 (autor principal del backend) y el equipo.

Este documento **no cambia código**. Reúne fallas encontradas y mejoras posibles, cada una con **por qué** importa y **cómo** se arreglaría. La idea es que se elijan algunas y se descarten otras; ninguna es obligatoria.

## Resumen

El backend está **bien hecho para su tamaño**: API pequeña y legible, `cargo test` y `clippy` limpios, contrato de datos claro, reglas de datos escritas y CI que valida JSON. Lo que más riesgo tiene **no está en el código Rust**, sino alrededor:

1. **El cron de "Actualizar datos" nunca se ha ejecutado** y, aunque se ejecute, no puede traer datos nuevos de lluvia: IMERG V07 terminó en septiembre de 2025.
2. **Los datos de lluvia podrían empezar en 1998**, no en 2000/2001 como dicen los docs: hay 2 años más de serie para las tendencias.
3. **El commit automático de datos salta la validación** (CI no se dispara con `GITHUB_TOKEN`).
4. **No hay forma documentada de desplegar** el binario actual en Vercel.
5. Detalles de la API: 404 sin cuerpo JSON, sin `Cache-Control`, sin apagado ordenado, sin logs.

## Prioridades

| # | Hallazgo | Severidad | Esfuerzo | Documento |
|---|---|---|---|---|
| 1 | El cron mensual nunca corre (el workflow no está en `main`) | Alta | 5 min | [03](03-ci-cd-y-repo.md#1-el-cron-de-datos-nunca-se-ejecuta) |
| 2 | IMERG V07 terminó en 2025-09: 2025 nunca será año completo | Alta | Decisión | [02](02-pipeline-y-datos.md#1-imerg-v07-ya-no-se-actualiza) |
| 3 | IMERG V07 mensual empieza en 1998-01, no en 2000-06 | Media | 10 min | [02](02-pipeline-y-datos.md#2-imerg-empieza-en-1998-no-en-2000) |
| 4 | El bot sube datos a `developer` sin pasar por `e2e` | Alta | 15 min | [03](03-ci-cd-y-repo.md#2-el-bot-sube-datos-sin-validarlos) |
| 5 | Sin camino de despliegue para el servidor Axum en Vercel | Alta | Decisión | [03](03-ci-cd-y-repo.md#3-no-hay-forma-de-desplegar-el-binario-en-vercel) |
| 6 | Promedio por departamento: Callao tiene 0 celdas POWER | Media | 1-2 h | [02](02-pipeline-y-datos.md#3-promedio-por-departamento-callao-no-tiene-celdas-power) |
| 7 | Dependencias Python sin versión ni lockfile | Media | 30 min | [02](02-pipeline-y-datos.md#6-dependencias-sin-versión) |
| 8 | Rutas inexistentes devuelven 404 vacío, no JSON | Baja | 10 min | [01](01-api-rust.md#1-404-sin-cuerpo-json) |
| 9 | Sin `Cache-Control` en datos inmutables | Media | 10 min | [01](01-api-rust.md#2-sin-cache-control) |
| 10 | Sin apagado ordenado ni logs de peticiones | Baja | 15 min | [01](01-api-rust.md#4-sin-apagado-ordenado) |
| 11 | El modelo acepta campos desconocidos en silencio | Baja | 5 min | [01](01-api-rust.md#5-campos-desconocidos-se-ignoran-en-silencio) |
| 12 | PR #18 se mezcló a una rama ya mezclada | Info | — | [03](03-ci-cd-y-repo.md#6-pr-18-quedó-huérfano) |
| 13 | Revisión del PR #21 (OpenAPI) | Media | — | [01](01-api-rust.md#8-notas-sobre-el-pr-21-openapi) |
| 14 | Flujo "static-first" con espejo generado desde la API | Propuesta | 1-2 h | [04](04-flujos-y-tecnologias.md) |

**Severidad:** *Alta* = puede romper la demo o dejar datos malos sin aviso. *Media* = afecta calidad o costo. *Baja* = pulido.

## Documentos

1. [`01-api-rust.md`](01-api-rust.md): la API Axum, línea por línea.
2. [`02-pipeline-y-datos.md`](02-pipeline-y-datos.md): scripts Python y los JSON.
3. [`03-ci-cd-y-repo.md`](03-ci-cd-y-repo.md): GitHub Actions, despliegue y flujo de ramas.
4. [`04-flujos-y-tecnologias.md`](04-flujos-y-tecnologias.md): proyectos parecidos, tecnologías actuales y un flujo propuesto.

## Cómo se revisó

- Lectura completa de `src/`, `tests/`, `pipeline/`, `.github/`, `docs/` y del PR #21.
- `cargo test` (8/8 en verde) y `cargo clippy -- -W clippy::pedantic` (solo avisos de estilo).
- La API se levantó en local y se probaron rutas límite (`/power/lima/`, rutas inexistentes, preflight CORS, `SIGTERM`).
- Fechas de IMERG verificadas en el catálogo oficial de NASA (CMR, colección `C2723754851-GES_DISC`) el 2026-11-14.
- Respuesta de NASA POWER con el año en curso probada contra la API real.
- Versiones de crates y acciones consultadas el 2026-11-14.

Lo que **no** se verificó: el repo de infraestructura (fuera del alcance de esta revisión) ni el despliegue real en Vercel.
