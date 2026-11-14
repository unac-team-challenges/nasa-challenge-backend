#!/usr/bin/env bash
# e2e: valida los datos, corre cargo test, compila, levanta la API y prueba los endpoints.
# Uso: bash tests/e2e.sh   (PORT para cambiar el puerto de prueba)
set -euo pipefail
cd "$(dirname "$0")/.."
PORT=${PORT:-3099}
URL=http://127.0.0.1:$PORT
fallos=0
ok()  { echo "ok   $1"; }
mal() { echo "FAIL $1"; fallos=1; }
chk() { local d=$1; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else mal "$d"; fi; }

echo "== datos"
chk "power.json es JSON válido con 25 regiones" jq -e 'length == 25' data/power.json
chk "todos los valores son números (sin null/NaN)" jq -e '[.[].anios[][]] | length > 0 and all(type == "number")' data/power.json
chk "gpm.json: lluvia entre 0 y 30 mm/día (detecta unidades mal)" jq -e '[.[].anios[].lluvia_mm_dia] | all(. >= 0 and . <= 30)' data/gpm.json
chk "power.json: T2M entre -15 y 35 °C"                           jq -e '[.[].anios[].T2M] | all(. >= -15 and . <= 35)' data/power.json
chk "power.json: PRECTOTCORR entre 0 y 30 mm/día"                 jq -e '[.[].anios[].PRECTOTCORR] | all(. >= 0 and . <= 30)' data/power.json
chk "pipeline/power.py compila" python3 -m py_compile pipeline/power.py
chk "gpm.json es JSON válido con 25 regiones" jq -e 'length == 25' data/gpm.json
chk "gpm.json: todos los valores son números (sin null/NaN)" jq -e '[.[].anios[][]] | length > 0 and all(type == "number")' data/gpm.json
chk "pipeline/gpm.py compila" python3 -m py_compile pipeline/gpm.py

echo "== tests de integración (cargo test)"
chk "cargo test" cargo test --quiet

echo "== api"
cargo build --quiet
PORT=$PORT ./target/debug/nasa-challenge-backend >/dev/null &
pid=$!
trap 'kill $pid 2>/dev/null || true' EXIT
for _ in $(seq 40); do curl -sf "$URL/regiones" >/dev/null && break; sleep 0.5; done

chk "GET /regiones devuelve 25"           bash -c "curl -sf $URL/regiones | jq -e 'length == 25'"
chk "GET /power/lima devuelve años"       bash -c "curl -sf $URL/power/lima | jq -e '.anios | length > 0'"
chk "GET /gpm/lima devuelve lluvia"       bash -c "curl -sf $URL/gpm/lima | jq -e '[.anios[].lluvia_mm_dia] | length > 0 and all(type == \"number\")'"
chk "GET /gpm/noexiste -> 404"            bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $URL/gpm/noexiste)\" = 404 ]"
chk "GET /api/variables"                  bash -c "curl -sf $URL/api/variables | jq -e 'map(.id) == [\"lluvia\",\"temperatura\"]'"
chk "GET /api/zonas?variable=lluvia (25)" bash -c "curl -sf '$URL/api/zonas?variable=lluvia' | jq -e 'length == 25 and .[0].id == \"01\"'"
chk "GET /api/zonas/15 (serie)"           bash -c "curl -sf '$URL/api/zonas/15?variable=temperatura' | jq -e '.nombre == \"Lima\" and (.serie | length > 0)'"
chk "GET /api/zonas sin variable -> 400"  bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $URL/api/zonas)\" = 400 ]"
chk "GET /power/%C3%81ncash (acentos)"    bash -c "curl -sf $URL/power/%C3%81ncash | jq -e '.region == \"Áncash\"'"
chk "GET /health"                         bash -c "curl -sf $URL/health | jq -e '.status == \"ok\"'"
chk "ruta inexistente -> 404 JSON"        bash -c "curl -s $URL/noexiste | jq -e '.error | type == \"string\"'"
chk "datos con Cache-Control"             bash -c "curl -si $URL/gpm/lima | grep -qi '^cache-control: public'"
chk "GET /power/ancash (sin tilde)"       bash -c "curl -sf $URL/power/ancash | jq -e '.region == \"Áncash\"'"
chk "GET /power/noexiste -> 404"          bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $URL/power/noexiste)\" = 404 ]"
chk "CORS permite localhost"              bash -c "curl -si -H 'Origin: http://localhost:5173' $URL/regiones | grep -qi '^access-control-allow-origin: http://localhost:5173'"
chk "CORS rechaza otros orígenes"         bash -c "! curl -si -H 'Origin: http://localhost.evil.com' $URL/regiones | grep -qi '^access-control-allow-origin'"

[ "$fallos" = 0 ] && echo "TODO OK" || { echo "HAY FALLOS"; exit 1; }
