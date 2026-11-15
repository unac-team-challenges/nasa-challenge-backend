# 03 · CI/CD, despliegue y flujo del repo

`CONDITIONS.md`, la plantilla de PR y el `e2e` que corre en cada PR son un nivel de orden poco común en un hackathon. Los hallazgos de aquí son sobre lo que **pasa de verdad** en GitHub, que no siempre coincide con lo escrito.

---

## 1. El cron de datos nunca se ejecuta

**Qué pasa.** GitHub solo dispara `schedule` desde la **rama por defecto**, y la rama por defecto del repo es `main`. El workflow `actualizar-datos.yml` ya existe en `main`, pero `main` está 19 commits detrás de `developer` y el 2026-11-14 `gh run list --workflow "Actualizar datos"` no mostraba ninguna ejecución:

Los datos nunca se han actualizado solos. Falta lanzarlo una vez a mano (`workflow_dispatch`) para comprobar que corre, con `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` como *secrets*.

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

## 4. CI: lo que falta y cuesta poco

| Añadir | Por qué | Cómo |
|---|---|---|
| `cargo fmt --check` y `cargo clippy -- -D warnings` | Hoy el estilo depende de cada persona; clippy está limpio, así que activarlo no cuesta nada | Dos líneas antes de `bash tests/e2e.sh` |
| `cargo-deny` (opcional) | Revisa licencias y avisos de seguridad de crates | `EmbarkStudios/cargo-deny-action@v2`. Opcional: con 5 dependencias el riesgo es bajo |

---

## 5. Protección de ramas en plan gratis

**Qué pasa.** `CONDITIONS.md` explica que GitHub no bloquea el merge porque el repo es privado en una organización gratis. Es correcto: las reglas de protección en repos privados necesitan GitHub Team.

**Opciones.**

- Seguir con la regla de equipo (lo actual). Es razonable durante el hackathon.
- Al terminar el evento, **hacer público el repo**: en repos públicos la protección de ramas y el *required check* `e2e` son gratis. Antes, revisar que no haya secretos en el historial (no se encontró ninguno en esta revisión).

**Además:** activar **"Automatically delete head branches"** (hoy `delete_branch_on_merge: false`; hay 20 ramas remotas, casi todas ya mezcladas). Ayuda también con el punto 6.

---

## 7. `main` como "producción"

`main` no se ha actualizado nunca. Si Vercel apunta a `main` para producción, hoy publicaría solo un README. Conviene decidir una fecha concreta para el primer `developer → main` (por ejemplo, el *code freeze* antes de la demo) y escribirla en `CONDITIONS.md`.
