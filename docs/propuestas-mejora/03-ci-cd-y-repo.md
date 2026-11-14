# 03 · CI/CD, despliegue y flujo del repo

`CONDITIONS.md`, la plantilla de PR y el `e2e` que corre en cada PR son un nivel de orden poco común en un hackathon. Los hallazgos de aquí son sobre lo que **pasa de verdad** en GitHub, que no siempre coincide con lo escrito.

---

## 1. El cron de datos nunca se ejecuta

**Qué pasa.** GitHub solo dispara `schedule` desde la **rama por defecto**, y la rama por defecto del repo es `main`. Hoy `main` tiene un solo commit ("Inicializa el repositorio con README") y está **44 commits detrás** de `developer`. El workflow `actualizar-datos.yml` no existe en `main`:

```text
$ gh run list --workflow "Actualizar datos"
could not find any workflows named Actualizar datos
```

El comentario del YAML lo anticipa ("el cron solo corre si este archivo está en main"), pero la consecuencia práctica es que **los datos nunca se han actualizado solos** y tampoco se puede lanzar a mano (`workflow_dispatch` también necesita el archivo en la rama por defecto).

**Cómo (elegir una).**

- Mientras dure el hackathon: **cambiar la rama por defecto a `developer`** (Settings → General → Default branch). Es lo que el equipo usa de verdad.
- O hacer el primer PR `developer → main` ya, como dice `CONDITIONS.md`.

Antes de activarlo, leer el punto 2 y el [§1 de 02](02-pipeline-y-datos.md#1-imerg-v07-ya-no-se-actualiza): hoy correría ~2 horas para no cambiar nada en `gpm.json`.

---

## 2. El bot sube datos sin validarlos

**Qué pasa.** El job hace `git push` directo a `developer` usando el `GITHUB_TOKEN`. GitHub **no dispara otros workflows** con eventos creados por ese token (lo hace a propósito para evitar bucles). Resultado: el commit de datos **no pasa por `e2e`**.

**Por qué importa.** Choca con dos reglas del propio repo: "PR a `developer`" y "nadie mezcla con `e2e` en rojo". Si un día POWER devuelve algo raro, `data/*.json` cambia sin revisión y la API puede no arrancar en el siguiente despliegue.

**Cómo (lo mínimo).** Correr el `e2e` **en el mismo job, antes de hacer commit**:

```yaml
jobs:
  datos:
    runs-on: ubuntu-latest
    timeout-minutes: 90          # hoy hereda 360 min
    concurrency: actualizar-datos
    steps:
      # ...checkout, python, pipeline...
      - uses: Swatinem/rust-cache@v2
      - run: bash tests/e2e.sh   # si falla, no hay commit
      - name: Commit si cambió
        run: |
          # igual que hoy
```

**Cómo (mejor).** En vez de `git push`, abrir un PR con `gh pr create --base developer`. Así una persona ve el diff de datos antes de mezclar. Como ese PR tampoco dispara CI (mismo token), el `e2e` del paso anterior sigue siendo necesario. Si se quiere que el PR sí dispare CI, hace falta un token de GitHub App o un PAT guardado como *secret*.

---

## 3. No hay forma de desplegar el binario en Vercel

**Qué pasa.** El README dice "vista previa en Vercel", pero el repo no tiene `vercel.json`, ni `Dockerfile`, ni carpeta `api/`. `main.rs` abre un `TcpListener` y queda escuchando: es un **servidor de larga vida**. Las funciones de Vercel no funcionan así.

Opciones reales:

| Opción | Qué hace falta | Pros | Contras |
|---|---|---|---|
| **A. JSON estáticos en el CDN de Vercel** | Generar archivos desde la propia API (ver [04](04-flujos-y-tecnologias.md)) | Sin servidor, sin arranque en frío, gratis, nada que se caiga | No hay lógica en tiempo de petición (hoy tampoco se necesita) |
| B. Runtime Rust de Vercel | Crate `vercel_runtime`, punto de entrada en `api/`, `vercel.json` | Todo en Vercel | En **beta** según la documentación de Vercel; cambia el `main.rs` |
| C. Contenedor (Cloud Run, Fly.io, Render, o Docker en Vercel) | `Dockerfile` multi-etapa + apagado ordenado ([01 §4](01-api-rust.md#4-sin-apagado-ordenado)) | El código actual sirve tal cual | Otra plataforma, otra cuenta, arranque en frío |

**Recomendación:** A como camino principal y el servidor Axum para desarrollo local. Es lo que ya insinúa el PR #21 ("el plan B estático la necesita en la ruta"): si el plan B sirve, que sea el plan A.

> Recordatorio de la auditoría del stack: el plan Hobby de Vercel **no conecta repos de una organización de GitHub**. Con cualquier opción, decidir antes quién despliega (cuenta personal, plan Pro, o `vercel deploy` desde Actions con token).

---

## 4. CI: lo que falta y cuesta poco

| Añadir | Por qué | Cómo |
|---|---|---|
| `cargo fmt --check` y `cargo clippy -- -D warnings` | Hoy el estilo depende de cada persona; clippy está limpio, así que activarlo no cuesta nada | Dos líneas antes de `bash tests/e2e.sh` |
| `permissions: contents: read` en `ci.yml` | El token del CI tiene permisos de escritura por defecto | Bloque `permissions` arriba del YAML |
| `concurrency` con `cancel-in-progress: true` | Varios *push* seguidos al mismo PR gastan minutos en paralelo | `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }` |
| Versiones de acciones | `checkout@v4` y `setup-python@v5`; ya existen v7 de ambas | Subir y, si se quiere más seguridad, fijar por SHA |
| Dependabot | Avisos de versiones nuevas y de seguridad para `cargo`, `pip` y `github-actions` | `.github/dependabot.yml`, frecuencia mensual para no hacer ruido |
| `cargo-deny` (opcional) | Revisa licencias y avisos de seguridad de crates | `EmbarkStudios/cargo-deny-action@v2`. Opcional: con 5 dependencias el riesgo es bajo |

---

## 5. Protección de ramas en plan gratis

**Qué pasa.** `CONDITIONS.md` explica que GitHub no bloquea el merge porque el repo es privado en una organización gratis. Es correcto: las reglas de protección en repos privados necesitan GitHub Team.

**Opciones.**

- Seguir con la regla de equipo (lo actual). Es razonable durante el hackathon.
- Al terminar el evento, **hacer público el repo**: en repos públicos la protección de ramas y el *required check* `e2e` son gratis. Antes, revisar que no haya secretos en el historial (no se encontró ninguno en esta revisión).

**Además:** activar **"Automatically delete head branches"** (hoy `delete_branch_on_merge: false`; hay 20 ramas remotas, casi todas ya mezcladas). Ayuda también con el punto 6.

---

## 6. PR #18 quedó huérfano

**Qué pasa.** El PR #16 (`feat/api-gpm → developer`) se mezcló a las 19:04:13. El PR #18 (`feat/api-contrato-drive → feat/api-gpm`) se mezcló **77 segundos después**, sobre una rama que ya estaba mezclada. Sus commits (`419b1a8`, rutas `/api/variables` y `/api/zonas`) **no están en `developer`**. Hoy solo llegan a través del PR #21, que los incluye.

**Por qué importa.** No se perdió trabajo, pero fue suerte. Con PR apilados (uno sobre otro) es fácil que algo se quede fuera sin que nadie lo note.

**Cómo.** Con "Automatically delete head branches" activado, GitHub **cambia solo la base** de los PR que apuntaban a la rama borrada y los manda a `developer`. Es la forma nativa de evitar este caso, sin herramientas extra.

---

## 7. `main` como "producción"

`main` no se ha actualizado nunca. Si Vercel apunta a `main` para producción, hoy publicaría solo un README. Conviene decidir una fecha concreta para el primer `developer → main` (por ejemplo, el *code freeze* antes de la demo) y escribirla en `CONDITIONS.md`.
