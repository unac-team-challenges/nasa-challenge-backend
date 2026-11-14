# Guía para Sebastián: scripts de extracción de datos

Objetivo: scripts en `pipeline/` (repo `nasa-challenge-backend`) que descarguen lluvia y temperatura de las 25 regiones del Perú y escriban JSON en `data/`. El API Axum solo lee esos JSON. **El API nunca calcula en vivo.**

Referencia que ya funciona: `pipeline/power.py` (NASA POWER). Copia su estructura.

> Lo marcado con ⚠️ **no está verificado**: probar antes de dar por bueno.

---

## 1. Qué fuentes usar

| Variable | Fuente recomendada | Alternativa | Credenciales |
|---|---|---|---|
| Lluvia | **GPM IMERG** (`GPM_3IMERGM` v07), ~10 km, desde 2000 | **CHIRPS v2**, ~5 km, desde 1981 | GPM: Earthdata. CHIRPS: ninguna |
| Temperatura | **MERRA-2** (`M2TMNXSLV`, variable `T2M`), ~50 km | POWER `T2M` (usa MERRA-2 por debajo) | MERRA-2: Earthdata. POWER: ninguna |
| Ya hecho | POWER (`PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`) en `pipeline/power.py` | | Ninguna |

Orden sugerido: **1) GPM, 2) MERRA-2, 3) CHIRPS** (opcional, para comparar).

---

## 2. Contrato de salida (no cambiarlo)

Un archivo por fuente en `data/` (`gpm.json`, `merra2.json`, `chirps.json`), con la misma forma que `data/power.json`:

```json
[
  {
    "region": "Piura", "lat": -5.19, "lon": -80.63,
    "anios": { "2017": { "lluvia_mm_dia": 1.84 }, "2018": { "lluvia_mm_dia": 0.22 } }
  }
]
```

Reglas:
- Las **25 regiones**, mismos nombres y coordenadas que en `power.py` (`REGIONES`). Importar esa lista, no copiarla.
- Nombre de variable **con unidad**: `lluvia_mm_dia`, `temp_c`.
- Promedio anual de los meses disponibles. Meses sin dato fuera del promedio; solo años completos. **Nunca `NaN` ni 0 en el JSON** (`json.dumps(..., allow_nan=False)`).
- Redondear a 4 decimales.

---

## 3. Credenciales (Earthdata) para GPM y MERRA-2

1. Cuenta gratis en https://urs.earthdata.nasa.gov.
2. En local: `cp .env.example .env` y rellena. `.env` está en la raíz del repo y en `.gitignore` (**nunca commitear**):
   ```
   EARTHDATA_USERNAME=...
   EARTHDATA_PASSWORD=...
   ```
3. En el script:
   ```python
   import earthaccess
   from dotenv import load_dotenv
   load_dotenv()
   earthaccess.login(strategy="environment")
   ```
4. En GitHub Actions: guardar los mismos dos valores como **secrets** del repo y pasarlos como `env` en el paso del pipeline (`.github/workflows/actualizar-datos.yml`).

Prueba rápida que ya funciona: buscar `GPM_3IMERGM`, `version="07"`, 1 mes, `count=1` devuelve 1 resultado.

---

## 4. GPM IMERG (lluvia)

- Búsqueda: `earthaccess.search_data(short_name="GPM_3IMERGM", version="07", temporal=("2001-01-01", "2024-12-31"))`. Un archivo por mes, ~18 MB cada uno.
- Formato: **HDF5**. ⚠️ Abrir con `xarray.open_dataset(ruta, group="Grid")` y leer la variable `precipitation`. Comprobar el nombre exacto de la variable y de las dimensiones en un archivo real.
- **Unidad: mm/hora.** Multiplicar por 24 para mm/día (y así compararla con POWER).
- Sacar el punto de cada región con `.sel(lat=..., lon=..., method="nearest")`.
- Los meses más recientes son **provisionales**: NASA los corrige después. Por eso se regenera cada mes.
- Los satélites fallan más en montaña (Cusco, Puno, Huancavelica): tenerlo en cuenta al interpretar.

## 5. MERRA-2 (temperatura)

- `short_name="M2TMNXSLV"`, variable `T2M`. Un archivo por mes, ~75 MB (94 variables dentro), malla 0.5° × 0.625°, longitudes de -180 a 180.
- **Unidad: Kelvin.** Restar 273.15 para °C.
- Descargar 72 meses completos son unos 5 GB. ⚠️ Mejor probar `earthaccess.open()` (lectura remota) con `xarray.open_dataset(f, engine="h5netcdf")` para leer solo `T2M`, y borrar lo descargado al terminar. Si no funciona, descargar mes a mes y borrar cada archivo tras leerlo.
- **Decidido (2026-11-14):** la temperatura es MERRA-2 vía POWER (`T2M`, `T2M_MAX`, `T2M_MIN`). Esta sección solo aplica si algún día se necesita otra variable de MERRA-2 que POWER no tenga.

## 6. CHIRPS v2 (opcional)

- Sin login. ⚠️ Archivos mensuales GeoTIFF en el servidor del Climate Hazards Center (UCSB), del estilo `.../CHIRPS-2.0/global_monthly/tifs/chirps-v2.0.YYYY.MM.tif.gz`. Verificar la URL real.
- Leer con `rasterio` y muestrear el punto de cada región. Unidad: **mm/mes**: dividir entre los días del mes para mm/día.
- Existe una versión más nueva (v3). ⚠️ Confirmar cuál conviene.

---

## 7. Estructura sugerida del script

```
pipeline/
  common.py        # REGIONES, función para escribir el JSON
  power.py         # ya existe
  gpm.py           # nuevo
  merra2.py        # nuevo
  requirements.txt # añadir earthaccess, python-dotenv, xarray, h5netcdf (y netCDF4 si hace falta)
```

Cada script: `python pipeline/gpm.py 2001 2024` → escribe `data/gpm.json`. Argumentos `inicio` y `fin` como en `power.py`.

## 8. Cómo probar que está bien

- 25 regiones y 6 años, sin vacíos inesperados.
- **Piura en 2017** debe salir claramente más lluvioso que 2016 y 2018 (Niño Costero). En POWER fue 1.84 mm/día frente a ~0.2–0.3.
- Lima y Callao pueden dar valores casi idénticos con POWER y MERRA-2 (misma celda de ~50 km). Con GPM y CHIRPS deberían diferir un poco.
- Costa sur (Tacna, Lima, Ica) con lluvia cercana a 0; Loreto y Madre de Dios las más altas.
- Si un valor de lluvia sale en miles, falta convertir la unidad.

## 9. Flujo de trabajo en el repo

- Reglas de ramas, commits y PR: ver [`CONDITIONS.md`](../CONDITIONS.md).
- Una rama por script (`feat/pipeline-gpm`) y un PR hacia `developer`.
- No subir los archivos descargados (`.hdf5`, `.nc4`, `.tif`): solo el JSON final. Añadirlos a `.gitignore` si se guardan en local.
- Cuando el script funcione, añadir su línea a `.github/workflows/actualizar-datos.yml` y los secrets de Earthdata.
- Después, el API Axum podrá servir el JSON nuevo (se hace aparte).
