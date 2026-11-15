#!/usr/bin/env bash
# Checks de data/cobertura_arboles.json (como tests/checks_ndvi.sh). Los corre tests/e2e.sh.
# Uso: bash tests/checks_cobertura.sh [archivo]
set -uo pipefail
f=${1:-data/cobertura_arboles.json}
fallos=0
chk() { local d=$1; shift; if jq -e "$@" "$f" >/dev/null 2>&1; then echo "ok   $d"; else echo "FAIL $d"; fallos=1; fi; }
chk "cobertura_arboles.json: series numéricas (sin null/NaN)" '[.[].anios[][]] | length > 0 and all(type == "number" and (isnan | not))'
chk "cobertura_arboles.json: cobertura de árboles entre 0 y 100 %" '[.[].anios[].arboles_pct] | all(. >= 0 and . <= 100)'
chk "cobertura_arboles.json: solo años 2001–2024" '[.[].anios | keys[] | tonumber] | all(. >= 2001 and . <= 2024)'
chk "cobertura_arboles.json: stats numéricos (sin null/NaN) y status válido" 'all(.[].stats; ([to_entries[] | select(.key != "status" and .key != "aviso") | .value] | all(type == "number" and (isnan | not))) and (.status | IN("real","posible_casualidad","pocos_datos")))'
chk "cobertura_arboles.json: todo 'real' cumple el criterio único" 'all(.[].stats | select(.status == "real"); .q_value < 0.05 and (.ci_low > 0 or .ci_high < 0) and (.lag1 | fabs) <= 0.5)'
chk "cobertura_arboles.json: unidad geográfica explícita en cada zona" 'all(.[]; .unidad_geografica | test("no es el promedio del departamento"))'
exit $fallos
