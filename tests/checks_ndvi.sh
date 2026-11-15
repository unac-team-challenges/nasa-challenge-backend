#!/usr/bin/env bash
# Checks de data/ndvi.json. Los corre tests/e2e.sh y los prueba tests/test_ndvi_checks.py
# (que confirma que detectan cada rotura). Uso: bash tests/checks_ndvi.sh [archivo]
set -uo pipefail
f=${1:-data/ndvi.json}
fallos=0
chk() { local d=$1; shift; if jq -e "$@" "$f" >/dev/null 2>&1; then echo "ok   $d"; else echo "FAIL $d"; fallos=1; fi; }
chk "ndvi.json: series numéricas (sin null/NaN)" '[.[].serie[][]] | length > 0 and all(type == "number" and (isnan | not))'
chk "ndvi.json: NDVI entre -1 y 1" '[.[].serie[].ndvi_anual] | all(. >= -1 and . <= 1)'
chk "ndvi.json: solo años 2001–2024" '[.[].serie[].anio] | all(. >= 2001 and . <= 2024)'
chk "ndvi.json: stats numéricos (sin null/NaN) y status válido" 'all(.[].stats; ([to_entries[] | select(.key != "status" and .key != "aviso") | .value] | all(type == "number" and (isnan | not))) and (.status | IN("real","posible_casualidad","pocos_datos")))'
chk "ndvi.json: todo 'real' cumple el criterio único" 'all(.[].stats | select(.status == "real"); .q_value < 0.05 and (.ci_low > 0 or .ci_high < 0) and (.lag1 | fabs) <= 0.5)'
chk "ndvi.json: las 3 zonas, con id único" '[.[].id] == ["chavimochic","ica-villacuri","olmos"]'
chk "ndvi.json: lat/lon dentro de su recuadro" 'all(.[]; .bbox[0] <= .lon and .lon <= .bbox[2] and .bbox[1] <= .lat and .lat <= .bbox[3])'
chk "ndvi.json: unidad geográfica explícita en cada zona" 'all(.[]; .unidad_geografica | test("no es el promedio del departamento"))'
exit $fallos
