#!/usr/bin/env bash
# Verificación completa con salida corta (pensada para agentes: ahorra tokens).
# Corre e2e (datos + cargo test + API), formato, clippy y las autopruebas de Python.
# Imprime solo una línea por paso y, si algo falla, las últimas líneas útiles del log.
# El log completo queda en $LOG (por defecto /tmp/verificar-<rama>.log).
#
# Uso: bash tests/verificar.sh            # todo
#      bash tests/verificar.sh rapido     # sin e2e (sin compilar ni levantar la API)
set -uo pipefail
cd "$(dirname "$0")/.."
rama=$(git rev-parse --abbrev-ref HEAD 2>/dev/null | tr '/' '-')
LOG=${LOG:-/tmp/verificar-${rama:-local}.log}
: >"$LOG"
fallos=0

paso() {
  local nombre=$1; shift
  echo "### $nombre" >>"$LOG"
  if "$@" >>"$LOG" 2>&1; then
    echo "ok   $nombre"
  else
    echo "FAIL $nombre"
    fallos=1
    # Solo lo útil: líneas FAIL/error/warning/assert del último bloque, máx. 15
    sed -n "/^### $nombre\$/,\$p" "$LOG" | grep -E 'FAIL|error|Error|warning:|panicked|assert|Traceback|^diff ' | head -15 | sed 's/^/     /'
  fi
}

paso "python: compilan los scripts del pipeline" bash -c 'for f in pipeline/*.py; do python3 -m py_compile "$f" || exit 1; done'
paso "python: autoprueba lab5 (criterio de tendencia)" python3 -c "import sys; sys.path.insert(0, 'pipeline/exploracion/josue/scripts'); import lab5_tendencias as l; l.autoprueba()"
[ -f pipeline/ndvi.py ] && paso "python: autoprueba ndvi" python3 pipeline/ndvi.py autoprueba
# Formato: solo aviso. developer aún no está formateado con rustfmt y el CI no lo exige;
# reformatear el código del equipo en otro PR evita conflictos con las ramas abiertas.
sin_formato=$(cargo fmt --check -- --color never -l 2>/dev/null | sort -u | sed "s|$PWD/||" | tr '\n' ' ')
if [ -z "$sin_formato" ]; then echo "ok   rust: formato (cargo fmt)"; else echo "aviso rust: sin formatear (no bloquea): $sin_formato"; fi
paso "rust: clippy sin avisos" cargo clippy --quiet --all-targets -- -D warnings
if [ "${1:-}" != "rapido" ]; then
  paso "e2e (datos + cargo test + API)" bash tests/e2e.sh
fi

if [ "$fallos" = 0 ]; then echo "TODO OK (log: $LOG)"; else echo "HAY FALLOS (log completo: $LOG)"; exit 1; fi
