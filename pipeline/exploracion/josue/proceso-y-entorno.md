# Proceso, entorno y seguridad

## Entorno

| Pieza | Versión / detalle |
|---|---|
| Sistema | Arch Linux (laptop de Josue) |
| Python | 3.12, entorno virtual en `.venv` dentro de esta carpeta (creado con `uv`) |
| Paquetes | `earthaccess`, `xarray`, `h5netcdf`, `netcdf4`, `pandas`, `geopandas`, `regionmask`, `scipy`, `pymannkendall`, `statsmodels`, `matplotlib`, `dask`, `requests` |
| Bruno | 4.3.0 (Flatpak; la colección se abre desde `bruno/coleccion/`), formato OpenCollection YAML |
| CLI de Bruno | ❌ No se pudo instalar `@usebruno/cli`: el registro de npm no responde desde el entorno de trabajo (timeout). Se usó `correr_bruno.py`, que ejecuta los mismos `.yml` |

Instalación reproducible:

```bash
cd pipeline/exploracion/josue
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
mkdir -p data salida
curl -sL -o data/peru_departamental_simple.geojson \
  https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson
```

## Orden de ejecución

```bash
python3 scripts/lab1_power.py                        # 1. POWER en 5 puntos (solo biblioteca estándar)
python3 scripts/lab4_celdas_departamento.py          # 2. celdas por departamento
python3 scripts/lab5_tendencias.py                   # 3. tendencia en los 5 puntos (+ autoprueba)
.venv/bin/python scripts/power_departamentos.py      # 4. tendencias por departamento (umbral exigente)
.venv/bin/python scripts/validar_lab5.py             # 5. comparar con pymannkendall / scipy / statsmodels
.venv/bin/python scripts/correr_bruno.py bruno/coleccion           # 6. ejecutar la colección de Bruno
.venv/bin/python scripts/graficos.py                 # 7. PNG
.venv/bin/python scripts/lab2_imerg_gpcp.py          # 8. IMERG + GPCP (necesita credencial válida)
```

Detalle de cada script: [scripts/scripts.md](scripts/scripts.md).

## Fuentes y verificación

- Fechas, variables y unidades de IMERG, GPCP y MOD13A3: **catálogo CMR de NASA** (sin cuenta), consultado el 14 nov 2026.
- GeoJSON: `juaneladio/peru-geojson` → `peru_departamental_simple.geojson` (140 KB).
- POWER: API mensual (puntual y regional) v2.10.0, comunidad `AG`.
- Lo que no se pudo ejecutar está marcado como **no probado** o **bloqueado**.

## Seguridad y credenciales

- **Ninguna credencial en scripts, documentos ni colección de Bruno.** Bruno usa variables **secretas** (`edl_user`, `edl_pass`) que guarda cifradas fuera de los `.yml`. Los tokens se guardan solo en memoria (`bru.setEnvVar`).
- La credencial de Earthdata vive solo en `~/.netrc` (permiso 600) de la laptop. `earthaccess` la lee con `strategy="netrc"`.
- **Incidente registrado (14 nov 2026):** la contraseña de la cuenta **secundaria** de Earthdata de Josue se compartió en texto plano dentro de una sesión con un asistente de IA. **Decisión del dueño:** es una cuenta secundaria creada para el reto y no se rota. La contraseña **no** se copia en ningún archivo del proyecto ni del Drive. Si la cuenta se reutiliza fuera del reto, hay que cambiarla.
- **Estado de la cuenta:** el login falla (`{"error":"invalid_credentials"}`) en `earthaccess` y en AppEEARS. Causas posibles: registro sin terminar, correo sin verificar o contraseña cambiada. No se reintentó varias veces, para no bloquear la cuenta.
- No se suben datos pesados al Drive; solo scripts, documentos y resultados pequeños.
