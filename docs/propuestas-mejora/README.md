# Propuestas de mejora pendientes del backend

Estado al 2026-11-14. Lo que ya se aplicó (404 JSON, `Cache-Control`, apagado ordenado, `deny_unknown_fields`, rangos físicos en `e2e`, versiones fijas en `requirements.txt`, `permissions`/`concurrency`/dependabot en el CI, Callao, despliegue en Render) **se quitó de estos documentos**; su historia está en `changelog/`.

Este documento **no cambia código**: cada punto dice **por qué** importa y **cómo** se arreglaría. Ninguno es obligatorio.

## Pendientes

| # | Hallazgo | Severidad | Esfuerzo | Documento |
|---|---|---|---|---|
| 1 | Flujo «static-first» con espejo generado desde la API | Propuesta | 1-2 h | [04](04-flujos-y-tecnologias.md) |

Aplicado el 2026-11-15: ver `changelog/`.

**Severidad:** *Alta* = puede romper la demo o dejar datos malos sin aviso. *Media* = afecta calidad o costo. *Baja* = pulido.

## Documentos

1. [`02-pipeline-y-datos.md`](02-pipeline-y-datos.md): scripts Python y los JSON.
2. [`03-ci-cd-y-repo.md`](03-ci-cd-y-repo.md): GitHub Actions y flujo del repo.
3. [`04-flujos-y-tecnologias.md`](04-flujos-y-tecnologias.md): proyectos parecidos, tecnologías actuales y un flujo propuesto.
