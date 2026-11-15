#!/usr/bin/env bash
# e2e: valida los datos, corre cargo test, compila, levanta la API y prueba los endpoints.
# Uso: bash tests/e2e.sh   (PORT para cambiar el puerto de prueba)
set -euo pipefail
cd "$(dirname "$0")/.."
PORT=${PORT:-3099}
URL=http://127.0.0.1:$PORT
fallos=0
FIN=2024  # último año de las series (PERIODO en pipeline/tendencias.py); un solo sitio al añadir 2025
# Python con las dependencias de pipeline/requirements.txt: la .venv local si existe (el CI las instala
# en el python3 del sistema). Sin ellas fallan test_tendencias, test_pipeline y las autopruebas.
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
ok()  { echo "ok   $1"; }
mal() { echo "FAIL $1"; fallos=1; }
chk() { local d=$1; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else mal "$d"; fi; }

echo "== datos"
chk "power.json es JSON válido con 25 regiones" jq -e 'length == 25' data/power.json
chk "todos los valores son números (sin null/NaN)" jq -e '[.[].anios[][]] | length > 0 and all(type == "number" and (isnan | not))' data/power.json
chk "gpm.json: lluvia entre 0 y 30 mm/día (detecta unidades mal)" jq -e '[.[].anios[].lluvia_mm_dia] | all(. >= 0 and . <= 30)' data/gpm.json
chk "power.json: T2M entre -15 y 35 °C"                           jq -e '[.[].anios[].T2M] | all(. >= -15 and . <= 35)' data/power.json
chk "power.json: PRECTOTCORR entre 0 y 30 mm/día"                 jq -e '[.[].anios[].PRECTOTCORR] | all(. >= 0 and . <= 30)' data/power.json
chk "celdas/temperatura.json: celdas con T2M entre -15 y 35 °C"   jq -e '(.celdas | length > 100) and ([.celdas[].t2m[] | select(. != null)] | all(. >= -15 and . <= 35))' data/celdas/temperatura.json
chk "celdas/lluvia.json: celdas con valor (mm/año) entre 0 y 12 000"   jq -e '(.unidad == "mm/año") and (.celdas | length > 100) and ([.celdas[].valor[] | select(. != null)] | all(. >= 0 and . <= 12000))' data/celdas/lluvia.json
chk "celdas/vegetacion.json: ~2 000 celdas de 0,25° con NDVI entre -0,2 y 1" jq -e '(.unidad == "NDVI") and .dlat == 0.25 and (.celdas | length > 1500) and ([.celdas[].valor[] | select(. != null)] | all(. >= -0.2 and . <= 1)) and all(.celdas[]; [.valor[] | select(. != null)] | length > 0)' data/celdas/vegetacion.json
chk "ndvi_departamentos.json: 25 regiones con NDVI numérico" jq -e 'length == 25 and ([.[].anios[].ndvi] | all(type == "number" and . >= -0.2 and . <= 1))' data/ndvi_departamentos.json
chk "pipeline/vegetacion_malla.py: autoprueba (meses, celdas, null, departamentos)" "$PY" pipeline/vegetacion_malla.py autoprueba
chk "pipeline/power.py compila" "$PY" -m py_compile pipeline/power.py
chk "gpm.json es JSON válido con 25 regiones" jq -e 'length == 25' data/gpm.json
chk "gpm.json: todos los valores son números (sin null/NaN)" jq -e '[.[].anios[][]] | length > 0 and all(type == "number" and (isnan | not))' data/gpm.json
chk "pipeline/gpm.py compila" "$PY" -m py_compile pipeline/gpm.py
chk "pipeline/tendencias.py compila" "$PY" -m py_compile pipeline/tendencias.py
chk "tests/test_tendencias.py (semáforo, aviso, periodo)" "$PY" -m unittest -q tests/test_tendencias.py
chk "tests/test_pipeline.py (avisos e IMERG incremental)" "$PY" -m unittest -q tests/test_pipeline.py
chk "variables.json tiene lluvia, temperatura, lluvia_imerg y vegetacion" jq -e '[.[].id] == ["lluvia","temperatura","lluvia_imerg","vegetacion"]' data/variables.json
chk "variables.json: periodo 2001–$FIN, lluvia de POWER e IMERG aparte" jq -e --argjson fin $FIN 'all(.anio_inicio == 2001 and .anio_fin == $fin) and (.[0].fuente | test("POWER")) and (.[2].fuente | test("IMERG"))' data/variables.json
chk "celdas/vegetacion.json: 2001–$FIN, cada celda con un valor por año" jq -e --argjson fin $FIN '.anio_inicio == 2001 and .anio_fin == $fin and all(.celdas[]; (.valor | length) == $fin - 2001 + 1)' data/celdas/vegetacion.json
chk "zonas/lluvia_imerg.json: aviso del cambio de satélites de 2014 en las 25" jq -e 'all(.[].stats.aviso; type == "string" and test("2014"))' data/zonas/lluvia_imerg.json
chk "zonas/lluvia_imerg.json: ninguna zona 'real' (salto de 2014)" jq -e 'all(.[].stats.status; . != "real")' data/zonas/lluvia_imerg.json
chk "zonas/lluvia.json (POWER): sin el aviso de 2014 de IMERG" jq -e 'all(.[].stats; (.aviso // "") | test("2014") | not)' data/zonas/lluvia.json
for v in lluvia temperatura lluvia_imerg vegetacion; do
  chk "zonas/$v.json: todo 'real' cumple el criterio único (q<0.05, IC sin 0, |lag1|<=0.5)" jq -e 'all(.[].stats | select(.status == "real"); .q_value < 0.05 and (.ci_low > 0 or .ci_high < 0) and (.lag1 | fabs) <= 0.5)' data/zonas/$v.json
  chk "zonas/$v.json: 25 zonas con id 01–25" jq -e '[.[].id] == ([range(1;26)] | map(tostring | if length == 1 then "0" + . else . end))' data/zonas/$v.json
  chk "zonas/$v.json: stats numéricos (sin null/NaN)" jq -e '[.[].stats | to_entries[] | select(.key != "status" and .key != "aviso") | .value] | all(type == "number" and (isnan | not))' data/zonas/$v.json
  chk "zonas/$v.json: periodo 2001–$FIN" jq -e --argjson fin $FIN 'all(.[].stats; .year_start == 2001 and .year_end == $fin)' data/zonas/$v.json
  chk "zonas/$v.json: status válido" jq -e 'all(.[].stats.status; IN("real","posible_casualidad","pocos_datos"))' data/zonas/$v.json
  chk "zonas/$v/: 25 fichas con serie numérica" bash -c "ls data/zonas/$v/*.json | wc -l | grep -qx 25 && jq -s -e 'all(.[].serie[]; (.anio|type==\"number\") and (.valor|type==\"number\"))' data/zonas/$v/*.json"
done
chk "pipeline/appeears.py compila" "$PY" -m py_compile pipeline/appeears.py
chk "pipeline/ndvi.py compila" "$PY" -m py_compile pipeline/ndvi.py
chk "ndvi: autoprueba (años completos, BH, criterio único, sin NaN)" "$PY" pipeline/ndvi.py autoprueba
chk "tests/test_ndvi_checks.py (los checks de ndvi.json detectan 10 roturas)" "$PY" -m unittest -q tests/test_ndvi_checks.py
chk "lab5: autoprueba del criterio de tendencia" "$PY" -c "import sys; sys.path.insert(0, 'pipeline/exploracion/josue/scripts'); import lab5_tendencias as l; l.autoprueba()"
if [ -f data/ndvi.json ]; then
  bash tests/checks_ndvi.sh data/ndvi.json || fallos=1
else
  echo "aviso data/ndvi.json no existe todavía: falta generarlo (python pipeline/ndvi.py enviar|bajar|calcular)"
fi
chk "pipeline/cobertura.py compila" "$PY" -m py_compile pipeline/cobertura.py
chk "cobertura: autoprueba (años válidos, BH, criterio único, sin NaN, área)" "$PY" pipeline/cobertura.py autoprueba
bash tests/checks_cobertura.sh data/cobertura_arboles.json || fallos=1

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
chk "GET /api/variables"                  bash -c "curl -sf $URL/api/variables | jq -e 'map(.id) == [\"lluvia\",\"temperatura\",\"lluvia_imerg\",\"vegetacion\"]'"
chk "GET /api/zonas?variable=lluvia (25)" bash -c "curl -sf '$URL/api/zonas?variable=lluvia' | jq -e 'length == 25 and .[0].id == \"01\"'"
chk "GET /api/zonas/15 (serie)"           bash -c "curl -sf '$URL/api/zonas/15?variable=temperatura' | jq -e '.nombre == \"Lima\" and (.serie | length > 0)'"
chk "GET /api/zonas/07 lleva nota"           bash -c "curl -sf '$URL/api/zonas/07?variable=temperatura' | jq -e '.nota | type == \"string\"'"
chk "GET /api/zonas trae stats.status válido" bash -c "curl -sf '$URL/api/zonas?variable=lluvia' | jq -e 'length == 25 and all(.[].stats.status; IN(\"real\",\"posible_casualidad\",\"pocos_datos\"))'"
chk "GET /api/zonas/15 lluvia_imerg: aviso 2014" bash -c "curl -sf '$URL/api/zonas/15?variable=lluvia_imerg' | jq -e '(.stats.aviso | test(\"2014\")) and (.stats.q_value | type == \"number\")'"
chk "GET /api/zonas/15 temperatura sin aviso" bash -c "curl -sf '$URL/api/zonas/15?variable=temperatura' | jq -e '.stats.status and (.stats | has(\"aviso\") | not)'"
chk "GET /api/zonas/25 temperatura: aviso propio de Ucayali" bash -c "curl -sf '$URL/api/zonas/25?variable=temperatura' | jq -e '.stats.status == \"real\" and (.stats.aviso | test(\"2023 y 2024\"))'"
chk "GET /api/vegetacion (Caso 2)"         bash -c "curl -sf $URL/api/vegetacion | jq -e 'length >= 2 and all(.[]; (.unidad_geografica | type == \"string\") and (.stats.status | IN(\"real\",\"posible_casualidad\",\"pocos_datos\")))'"
chk "GET /api/cobertura-arboles (selva)"   bash -c "curl -sf $URL/api/cobertura-arboles | jq -e 'length >= 2 and all(.[]; (.unidad_geografica | type == \"string\") and (.stats.status | IN(\"real\",\"posible_casualidad\",\"pocos_datos\")))'"
chk "GET /api/celdas?variable=temperatura" bash -c "curl -sf '$URL/api/celdas?variable=temperatura' | jq -e '.celdas | length > 100'"
chk "GET /api/celdas?variable=lluvia (mm/año)" bash -c "curl -sf '$URL/api/celdas?variable=lluvia' | jq -e '.unidad == \"mm/año\" and (.celdas | length > 100)'"
chk "GET /api/celdas?variable=vegetacion (NDVI, 0,25°)" bash -c "curl -sf '$URL/api/celdas?variable=vegetacion' | jq -e '.unidad == \"NDVI\" and .dlat == 0.25 and (.celdas | length > 1500)'"
chk "GET /api/zonas?variable=vegetacion (25)" bash -c "curl -sf '$URL/api/zonas?variable=vegetacion' | jq -e 'length == 25 and all(.[].stats.status; IN(\"real\",\"posible_casualidad\",\"pocos_datos\"))'"
chk "GET /api/celdas?variable=lluvia_imerg -> 400" bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' '$URL/api/celdas?variable=lluvia_imerg')\" = 400 ]"
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
