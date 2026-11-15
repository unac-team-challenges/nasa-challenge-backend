# Resultados de la tanda 3 (2026-11-15)

Fuente de las tareas: `tarea_favio_haiku_3.md`.

## Tarea 1: recordar el tema claro/oscuro (frontend)
- **Estado:** hecha, sin commit y sin push.
- **Dónde:** worktree `nasa-front-recordar-tema`, rama `feat/recordar-tema` (desde `origin/developer`), en la máquina donde se hizo. No está en el remoto ni en la máquina de Leandro (2026-11-15): si se pierde ese worktree, se pierde el trabajo.
- **Siguiente paso:** commit y push de la rama (o adjuntar el parche) para poder revisar las 138 pruebas.
- **Cambios:**
  - `src/stores/app.ts`: el tema se guarda en `localStorage` al alternarlo y se lee al cargar, dentro de `try/catch`.
  - `src/stores/app.test.ts` (nuevo).
  - `changelog/feat-recordar-tema.md` (nuevo).
- **Verificado:** `pnpm lint` limpio, `pnpm test --run` con 138 pruebas pasando, `pnpm build` correcto.
- **Pendiente:** el idioma no se guarda (solo va en la URL). Falta una prueba que cubra la lectura al cargar la página.

## Tarea 2: inventario de los clones `fe-*`
- **Estado:** pendiente.
- **Motivo:** se intentó desde un entorno aislado (sandbox) donde no existe `/home/leandro-rojas/Escritorio/Nasa`. En la máquina de Leandro las carpetas `fe-*` y `nasa-frontend-*` sí existen.
- **Siguiente paso:** correrla en la máquina de Leandro.

## Tarea 3: contrato del frontend contra el backend
- **Estado:** hecha (solo lectura).
- **Resultado:** el `openapi.json` del front en `origin/developer` está desactualizado frente al backend. Las diferencias están solo en `/api/celdas`:
  - el parámetro `variable` acepta `vegetacion` en el backend y no en el front;
  - el backend tiene un campo `valor` y un campo `nota` que el front no tiene;
  - en el front `t2m` es obligatorio; en el backend no.
- **Riesgo:** `pnpm gen` genera `src/api/schema.d.ts` desde el `src/api/openapi.json` del front. Si ese archivo sigue viejo, el esquema regenerado pierde estos tres cambios.
- **Siguiente paso:** copiar el `openapi.json` del backend sobre `src/api/openapi.json` del front y luego correr `pnpm gen`.

## Tarea 4: cabecera a 320 y 390 px
- **Estado:** hecha (solo medición).
- **Resultado:** en `origin/developer` en `3d7445a` (merge del PR #53), el `<header>` mide **117 px** a 320 px y a 390 px.
- **Capturas:** `cabecera-320.png` y `cabecera-390.png`, hechas en el sandbox. No están commiteadas, así que no hay evidencia visible.
- **Nota:** el changelog `fix-boton-idioma` dice 159 px a 320 px. En `3d7445a` no se reproduce: `ES | EN` y el tema caben en la primera fila.
- **Pendiente:** `developer` del front ya avanzó (hoy `5a84c59`). Remedir ahí antes de descartar el seguimiento de #36.
