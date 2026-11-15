# 04 · Proyectos parecidos, tecnologías actuales y un flujo propuesto

Este documento mira el backend desde afuera: cómo resuelven el mismo problema proyectos más grandes, qué tecnologías actuales encajan, y **cuáles no conviene adoptar**.

---

## 1. Qué hacen proyectos parecidos

El problema de fondo es "**datos climáticos procesados una vez, consultados muchas veces**". Varios proyectos públicos lo resuelven de forma parecida:

| Proyecto | Cómo lo resuelve | Qué se puede copiar |
|---|---|---|
| **Our World in Data — ETL** (`owid/etl`) | Pasos con nombre: `snapshot` (dato crudo guardado y con versión) → `meadow` (limpieza) → `garden` (armonizado, listo para análisis) → `grapher` (lo que se publica). Cada paso solo depende del anterior. | Separar **dato crudo** de **dato derivado**. Hoy `gpm.py` descarga, promedia y escribe en un solo paso: si cambia el método (píxel → departamento), hay que volver a bajar todo. |
| **World Bank — Climate Change Knowledge Portal** | Estadísticas por país y región **precalculadas** (CMIP, ERA5) que el portal solo muestra | Lo mismo que hace este repo: confirma que "la API nunca calcula" es la decisión correcta |
| **NASA POWER** | API sobre datos precalculados, con un endpoint de climatología y otro regional | Se puede reutilizar directamente |
| **Ecosistema Pangeo** (xarray, earthaccess, VirtualiZarr) | Leer datos de la nube sin descargarlos completos | Útil solo si se reprocesa a menudo (ver §3) |

**Lección común:** ninguno de estos proyectos calcula en el momento de la petición, y casi todos sirven **archivos estáticos detrás de un CDN** para lo que no cambia.

---

## 2. Flujo propuesto: "static-first" con espejo generado desde la API

### Problema

Hoy hay dos caminos para servir los mismos datos:

1. La API Axum (`/power/lima`, `/api/zonas/15?variable=lluvia`).
2. Un plan B de JSON estáticos que el frontend leería si la API falla.

Si los dos se escriben a mano, **se van a desalinear**: un campo renombrado en Rust no llega al plan B, y el fallo aparece justo cuando se necesita el plan B.

### Propuesta

**Generar el plan B desde el mismo router de Axum.** Un binario pequeño recorre todas las rutas, llama al router en memoria (igual que ya hacen los tests con `oneshot`) y guarda cada respuesta como archivo:

```text
pipeline/*.py ──> data/*.json ──(include_str!)──> router Axum
                                                     │
                       ┌─────────────────────────────┴───────────────────────┐
                       │                                                     │
              cargo run (local)                        cargo run --bin exportar
              servidor en :3000                        public/api/zonas/15/lluvia.json
                                                       public/api/variables.json
                                                       public/api/openapi.json
                                                                 │
                                                       CDN de Vercel (sin servidor)
```

```rust
// src/bin/exportar.rs  (≈ 30 líneas, sin dependencias nuevas: `tower` pasa a [dependencies])
use axum::{body::{to_bytes, Body}, http::Request};
use nasa_challenge_backend::{app, data::Datos};
use std::{fs, path::Path, sync::Arc};
use tower::ServiceExt;

#[tokio::main]
async fn main() {
    let router = app(Arc::new(Datos::cargar().unwrap()), vec![]);
    let mut rutas = vec![("/api/variables".to_string(), "api/variables.json".to_string())];
    for id in (1..=25).map(|n| format!("{n:02}")) {    // ubigeos "01".."25"
        for v in ["lluvia", "temperatura"] {
            rutas.push((format!("/api/zonas/{id}?variable={v}"), format!("api/zonas/{id}/{v}.json")));
        }
    }
    for (ruta, archivo) in rutas {
        let res = router.clone().oneshot(Request::get(&ruta).body(Body::empty()).unwrap()).await.unwrap();
        assert!(res.status().is_success(), "{ruta} -> {}", res.status());
        let destino = Path::new("public").join(archivo);
        fs::create_dir_all(destino.parent().unwrap()).unwrap();
        fs::write(destino, to_bytes(res.into_body(), usize::MAX).await.unwrap()).unwrap();
    }
}
```

### Por qué

- **Un solo contrato.** Los bytes del CDN son los mismos que devuelve la API, porque salen del mismo código. El test `openapi_json_esta_al_dia` del PR #21 sigue cuidando el contrato.
- **Sin punto único de fallo.** Un CDN no tiene arranque en frío, ni límite de invocaciones del plan Hobby, ni runtime en beta.
- **No se pierde nada de Rust.** Los modelos, la validación al cargar (`serde` + `deny_unknown_fields`) y los tests siguen siendo el filtro de calidad. Rust pasa de "servidor" a "compilador del contrato".
- **El servidor sigue existiendo** para desarrollo local y por si algún día hace falta lógica en tiempo de petición.

### Cómo probarlo

```bash
cargo run --bin exportar
npx serve public    # o: python -m http.server -d public
curl localhost:3000/api/zonas/15/lluvia.json
```

En el CI: correr `exportar` y comparar con `diff` contra lo publicado, o subir `public/` como artefacto.

> Nota: un archivo estático no puede leer `?variable=`, por eso la variable va en la ruta (`/15/lluvia.json`). El PR #21 ya contempla esto.

---

## 3. Tecnologías actuales que encajan

Ordenadas de más a menos útiles **para este proyecto y este plazo**.

| Tecnología | Para qué | Encaja porque | Cuándo adoptarla |
|---|---|---|---|
| **`uv`** (Astral) | Entorno y *lockfile* de Python | Un comando instala versiones exactas; mucho más rápido que `pip` | Versiones fijas en `requirements.txt` (hecho); `uv` queda opcional |
| **`regionmask.mask_3D_frac_approx`** | Promedio por departamento con celdas parciales | Resuelve Callao y Tumbes; `regionmask` ya está en la exploración | Con la tarea del promedio por departamento |
| **`scipy.stats.false_discovery_control`** | Benjamini-Hochberg | Evita instalar `statsmodels` solo para BH (SciPy ≥ 1.11) | Con `pipeline/tendencias.py` |
| **`scipy.stats.kendalltau` + `theilslopes`** | Mann-Kendall y pendiente de Sen | `pymannkendall` no publica versiones desde 2021. Para TFPW se puede seguir usándolo, pero con versión fijada y un test contra una serie conocida | Con `tendencias.py` |
| **NASA Harmony** (`harmony-py`) | Bajar solo la caja de Perú de IMERG | Verificado: `GPM_3IMERGM` admite recorte espacial y por variable | Si se reprocesa IMERG varias veces |
| **`tower-http`** (`SetResponseHeaderLayer`, `NormalizePathLayer`) | Caché y barra final | Ya es dependencia | Ya (hecho) |
| **`ruff`** | Lint y formato de Python | Un binario, sin configuración | Cuando haya más de 2 scripts |
| **`utoipa` 6 + `openapi-typescript`** | Tipos del frontend desde Rust | Ya planeado en el stack | Con el PR #21 |
| **VirtualiZarr / `earthaccess.virtualize`** | Leer HDF5 de la nube como si fuera Zarr, sin descargar | Muy potente para series largas | **No ahora**: 300 archivos mensuales no lo justifican |

---

## 4. Qué **no** adoptar (y por qué)

| Tentación | Por qué no |
|---|---|
| Base de datos (Postgres, SQLite, DuckDB) | Son ≈ 100 KB de datos inmutables. `include_str!` es más rápido y no tiene nada que configurar |
| GraphQL / tRPC | 3–6 rutas de solo lectura. OpenAPI ya da tipos al frontend |
| Kubernetes, Docker Compose, microservicios | Un binario o una carpeta de archivos estáticos |
| Dask, Spark, Polars | 25 regiones × 27 años. `pandas`/`xarray` sobran |
| Guardar los datos en Zarr/Parquet para la API | La API sirve JSON; convertir solo añade un paso |
| Autenticación, *rate limiting* | Datos públicos, solo lectura y detrás de un CDN. El CDN ya absorbe el abuso |
| Un `common.py` o una clase "Fuente" abstracta | Con 2 scripts, la duplicación es de 5 líneas. Hacerlo con la 3.ª fuente |

---

## 5. Orden sugerido

Si se aceptan las propuestas, este orden minimiza riesgo antes de la demo:

1. **Decisiones** (10 min de reunión): rama por defecto, qué hacer con IMERG V07 y la opción de despliegue (A, B o C).
2. **Arreglos de una línea**: `fallback` JSON, `Cache-Control`, `deny_unknown_fields`, rangos en `e2e.sh`, `fmt` + `clippy` en CI.
3. **Workflow de datos**: `e2e` antes del commit, `timeout-minutes`, GPM incremental o fuera del cron.
4. **Datos**: `gpm.py 1998 2024`, corregir los docs de fechas.
5. **Espejo estático** (`exportar`) si se elige la opción A.
6. **Después del hackathon**: `uv`, Dependabot, repo público con protección de ramas, `utoipa` 6 y `tower-http` 0.7.

---

## Fuentes

- Catálogo CMR de NASA, colección `GPM_3IMERGM` v07 (`C2723754851-GES_DISC`): fechas, `cloud_hosted` y servicios Harmony. Consultado el 2026-11-14.
- [Our World in Data — ETL: flujo de trabajo](https://owid-docs.readthedocs.io/projects/etl/architecture/workflow/)
- [regionmask — `mask_3D_frac_approx`](https://regionmask.readthedocs.io/en/stable/notebooks/mask_3D_frac_approx.html)
- [Earthdata Cloud Cookbook — Harmony](https://nasa-openscapes.github.io/earthdata-cloud-cookbook/tutorials/Harmony.html)
- [earthaccess — conjuntos virtuales](https://earthaccess.readthedocs.io/en/stable/user/tutorials/virtual_dataset_tutorial_with_TEMPO_Level3/)
- [Vercel — runtime de Rust](https://vercel.com/docs/functions/runtimes/rust) y [guía de Rust con Docker](https://vercel.com/kb/guide/deploy-rust-on-vercel-with-docker)
- [GitHub — `GITHUB_TOKEN` no dispara workflows](https://docs.github.com/en/actions/concepts/security/github_token)
- `docs/` de este repo (decisiones previas del equipo).
