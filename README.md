# nasa-challenge-backend

Detective del Perú · NASA Space Apps Challenge 2026 (equipo NASA-CHALLENGE-UNAC).

Pipeline de datos (Python) y API de solo lectura que sirve los JSON ya procesados. Los datos se calculan antes y la API nunca calcula en vivo.

## Ramas
- `developer`: aquí se integra todo (vista previa en Vercel).
- `main`: solo lo que ya funciona (producción). Se actualiza únicamente con pull request desde `developer`.

## Estructura
- `pipeline/power.py`: descarga NASA POWER (lluvia `PRECTOTCORR` mm/día y temperatura `T2M` °C) de las 25 regiones y escribe `data/power.json`.
- `data/power.json`: datos ya procesados (promedio anual por región).
- `src/main.rs`: API Axum de solo lectura; embebe `data/power.json` al compilar.

## Uso
```bash
pip install -r pipeline/requirements.txt
python pipeline/power.py 2015 2020   # regenera data/power.json
cargo run                            # http://0.0.0.0:3000 (PORT para cambiarlo)
```

Nota: NASA POWER tiene grilla de ~50 km, así que Lima y Callao caen en la misma celda y tienen datos idénticos. Se deja así.

CORS: la API solo acepta orígenes `localhost`/`127.0.0.1`; añadir la URL de Vercel en `origen_permitido` (`src/main.rs`).

| Endpoint | Respuesta |
|---|---|
| `GET /regiones` | Lista de regiones con lat/lon |
| `GET /power/{region}` | Promedios anuales de la región (404 si no existe) |
