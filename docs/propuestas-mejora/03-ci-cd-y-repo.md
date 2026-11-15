# 03 · CI/CD, despliegue y flujo del repo

`CONDITIONS.md`, la plantilla de PR y el `e2e` que corre en cada PR son un nivel de orden poco común en un hackathon. Los hallazgos de aquí son sobre lo que **pasa de verdad** en GitHub, que no siempre coincide con lo escrito.

---

## 2. El PR del bot no dispara el CI

**Qué pasa.** `actualizar-datos.yml` corre `bash tests/e2e.sh` en el mismo job y abre un PR a `developer`; ya no hace `git push` directo. Pero GitHub **no dispara otros workflows** con eventos creados por `GITHUB_TOKEN` (a propósito, para evitar bucles), así que el PR del bot no pasa por el `e2e` del CI.

**Por qué importa.** El `e2e` del job ya cubre lo esencial, pero el PR no queda con el check requerido y una persona tiene que revisar el diff de `data/` antes de mezclar.

**Cómo (si se quiere que el PR sí dispare CI).** Usar un token de GitHub App o un PAT guardado como *secret* en vez de `GITHUB_TOKEN`.

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

**Además:** activar **"Automatically delete head branches"** (hoy `delete_branch_on_merge: false`; hay 20 ramas remotas, casi todas ya mezcladas).
