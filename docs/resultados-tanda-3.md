# Resultados de la tanda 3 (2026-11-15)

Fuente de las tareas: `tarea_favio_haiku_3.md`.

## Tarea 1: recordar el tema claro/oscuro (frontend)
- **Estado:** hecha, sin commit.
- **Dónde:** worktree `nasa-front-recordar-tema`, rama `feat/recordar-tema` (desde `origin/developer`).
- **Cambios:**
  - `src/stores/app.ts`: el tema se guarda en `localStorage` al alternarlo y se lee al cargar, dentro de `try/catch`.
  - `src/stores/app.test.ts` (nuevo).
  - `changelog/feat-recordar-tema.md` (nuevo).
- **Verificado:** `pnpm lint` limpio, `pnpm test --run` con 138 pruebas pasando, `pnpm build` correcto.
- **Pendiente:** el idioma no se guarda (solo va en la URL). Falta una prueba que cubra la lectura al cargar la página.

## Tarea 2: inventario de los clones `fe-*`
- **Estado:** no se pudo hacer aquí.
- **Motivo:** las rutas son `/home/leandro-rojas/Escritorio/Nasa`, que no existe en esta máquina. Tampoco hay carpetas `fe-*` ni `nasa-frontend-*`.
- **Siguiente paso:** correrla en la máquina de Leandro.

## Tarea 3: contrato del frontend contra el backend
- **Estado:** hecha (solo lectura).
- **Resultado:** el `openapi.json` del front en `origin/developer` está desactualizado frente al backend. Las diferencias están solo en `/api/celdas`:
  - el parámetro `variable` acepta `vegetacion` en el backend y no en el front;
  - el backend tiene un campo `valor` y un campo `nota` que el front no tiene;
  - en el front `t2m` es obligatorio; en el backend no.
- **Riesgo:** al regenerar con `pnpm gen` se perderían estos cambios.

## Tarea 4: cabecera a 320 y 390 px
- **Estado:** hecha (solo medición).
- **Resultado:** en `origin/developer` (`3d7445a`), el `<header>` mide **117 px** a 320 px y a 390 px.
- **Capturas:**
  - `scratchpad\cabecera-320.png`
  - `scratchpad\cabecera-390.png`
- **Nota:** el changelog `fix-boton-idioma` dice 159 px a 320 px. Hoy no se reproduce: `ES | EN` y el tema caben en la primera fila.
