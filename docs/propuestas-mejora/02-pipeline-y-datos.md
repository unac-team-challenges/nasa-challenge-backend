# 02 · Pipeline Python y datos

Los dos scripts (`power.py`, `gpm.py`) son cortos y cumplen las reglas de datos: años completos, nunca `NaN` y `allow_nan=False`. Los problemas importantes vienen **de las fuentes**, no del código.

---

## 1. IMERG V07 ya no se actualiza

**Qué pasa.** El catálogo oficial de NASA (CMR) declara la colección `GPM_3IMERGM` v07 con `time_end = 2025-09-30`. El último archivo disponible es **septiembre de 2025**. No hay otra versión publicada de `GPM_3IMERGM` en el catálogo a la fecha (2026-11-14).

```bash
curl -s "https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM" \
  | jq '.feed.entry[] | {version_id, time_start, time_end}'
# {"version_id":"07","time_start":"1998-01-01T00:00:00.000Z","time_end":"2025-09-30T23:59:59.999Z"}
```

**Por qué importa.**

- 2025 **nunca** tendrá 12 meses en V07, así que `gpm.json` se queda en 2024 para siempre. La regla "el año nuevo entra en enero siguiente" (`docs/reglas-datos.md` §1) no se cumple para la lluvia.
- El cron mensual (si llegara a correr, ver [03](03-ci-cd-y-repo.md#1-el-cron-de-datos-nunca-se-ejecuta)) bajaría **≈ 27 años × 12 meses × 18 MB ≈ 5,8 GB** cada mes para obtener exactamente el mismo resultado.
- Cuando salga una versión nueva (V08), **no se puede mezclar** con V07 en la misma serie: cambia el algoritmo y eso rompe una tendencia.

**Cómo.**

1. Documentar en `docs/reglas-datos.md` que la lluvia termina en 2024 mientras siga V07.
2. Quitar `gpm.py` del cron mensual, o hacerlo **incremental**: leer `data/gpm.json` y descargar solo los años que faltan.
3. Añadir un aviso barato: un paso del workflow que consulte CMR y falle (o abra un *issue*) si aparece una versión distinta de `07`. Cuando aparezca, se reprocesa **toda** la serie con la versión nueva.
4. **No** rellenar 2025 con IMERG *Late/Early*: son otro producto y violan la regla 3 (una fuente = un número).

---

## 2. IMERG empieza en 1998, no en 2000

**Qué pasa.** Los documentos no coinciden entre sí ni con los datos:

| Fuente | Dice |
|---|---|
| `docs/tendencias.md` | "2001–2024 (IMERG empieza en jun 2000)" |
| `docs/reglas-datos.md` | "IMERG v07 mensual empieza en ene 2000" |
| `data/gpm.json` | 2000–2024, **con 2000 completo** (12 meses) |
| CMR (NASA), verificado | `time_start = 1998-01-01`; 36 archivos entre 1998 y 2000 |

V06 empezaba en junio de 2000; **V07 se extendió hacia atrás hasta enero de 1998** con datos de la era TRMM.

**Por qué importa.** Dos años más de serie: 27 en vez de 25. Para Mann-Kendall con autocorrelación (TFPW), cada año suma potencia estadística. Además, 1998 incluye el final de El Niño 1997-98, un caso extremo en la costa norte.

**Cómo.**

```bash
python pipeline/gpm.py 1998 2024
```

y corregir los dos documentos.

> **Cuidado (por confirmar con Josue):** antes de 2014 IMERG se apoya en la constelación TRMM, que tiene otros sensores. Revisar las *release notes* de V07 por posibles saltos de homogeneidad antes de usar 1998–2013 para tendencias. Si hay duda, calcular la tendencia con y sin esos años y mostrar ambas.

---

## 3. Promedio por departamento: Callao no tiene celdas POWER

**Qué pasa.** El equipo decidió usar el **promedio del departamento** en vez del píxel de la capital (`docs/reglas-datos.md` §3b). El laboratorio 4 ya contó las celdas (`pipeline/exploracion/josue/resultados/lab4_celdas_departamento.csv`):

| Departamento | Celdas IMERG (0,1°) | Celdas POWER (0,5° × 0,625°) |
|---|---|---|
| Callao | 1 | **0** |
| Tumbes | 37 | 1 |
| Lambayeque | 118 | 3 |
| Loreto | 3054 | 97 |

Con una máscara de "centro de celda dentro del polígono", **Callao no tiene temperatura** y Tumbes queda con un solo valor.

Otro dato: la celda POWER que hoy representa "Lima" tiene una **altitud de 1195 m** (lo devuelve la propia API de POWER en `geometry.coordinates`). La celda mezcla costa y sierra, así que la `T2M` de "Lima" no es la de la ciudad.

**Por qué importa.** Sin un plan, el pipeline de departamento o deja a Callao fuera (rompe las 25 zonas que la API y los tests asumen) o produce `NaN`.

**Cómo.**

- Usar **máscara fraccional**: `regionmask.Regions.mask_3D_frac_approx` (regionmask ≥ 0.12). Da la fracción de cada celda dentro del polígono; con eso, Callao recibe una parte de la celda que lo toca. El ponderado recomendado por la documentación de regionmask es fracción × `cos(lat)`:

  ```python
  frac = regiones.mask_3D_frac_approx(ds)               # region × lat × lon, valores 0..1
  pesos = frac * np.cos(np.deg2rad(ds.lat))
  por_depto = ds["precipitation"].weighted(pesos.fillna(0)).mean(("lat", "lon"))
  ```

  Precisión ≈ 5 % según la documentación: suficiente para promedios.
- Si la fracción sigue siendo 0, usar la celda más cercana y añadir `"nota"` a la región (ya previsto en `reglas-datos.md` §4).
- Para POWER, en vez de 97 llamadas de punto para Loreto, probar el endpoint **regional** de POWER (`/api/temporal/monthly/regional`), que devuelve una malla dentro de una caja. ⚠️ No verificado aquí: confirmar límites de tamaño de la caja.

---

## 4. `power.py` no reintenta

**Qué pasa.** `gpm.py` tiene reintentos; `power.py` no. Son 25 llamadas seguidas a una API pública. Si una falla con un 503 pasajero, el script entero se cae.

**Cómo.** Sin dependencias nuevas, con el `Retry` de `urllib3` (ya viene con `requests`):

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sesion = requests.Session()
sesion.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])))
# y usar sesion.get(...) en anual()
```

---

## 5. Años descartados sin aviso

**Qué pasa.** Los dos scripts descartan años incompletos (correcto), pero **no dicen cuáles**. En `gpm.py`, si la búsqueda devolviera 13 archivos (un duplicado), `len(valores) == 12` falla y el año desaparece en silencio para las 25 regiones.

**Por qué importa.** Un año que falta cambia la pendiente de Sen y el `n_years`. Debe verse en el log del CI, no descubrirse en la demo.

**Cómo.**

```python
if len(granulos) != 12:
    print(f"AVISO {anio}: {len(granulos)} archivos (se esperaban 12)", file=sys.stderr)
...
faltan = [r for r in REGIONES if r not in promedios]
if faltan:
    print(f"AVISO {anio}: sin año completo en {faltan}", file=sys.stderr)
```

Y quitar `-W ignore` del workflow para no ocultar otros avisos.

---

## 6. Dependencias sin versión

**Qué pasa.** `pipeline/requirements.txt` lista `numpy`, `pandas`, `earthaccess`, etc. **sin versión** y no hay *lockfile*. Cada `pip install` puede traer una versión mayor nueva (pandas 3, numpy 2.x, earthaccess con cambios de API).

**Por qué importa.** El mismo script puede dar otro resultado, o fallar, en la máquina de cada persona y en el CI. Para un análisis de tendencias eso es un problema de reproducibilidad.

**Cómo (opción moderna).** [`uv`](https://docs.astral.sh/uv/) con `pyproject.toml` + `uv.lock`:

```bash
uv init --bare --python 3.12
uv add numpy pandas requests earthaccess python-dotenv xarray h5netcdf h5py
uv run pipeline/power.py 2000 2025
```

En el workflow: `astral-sh/setup-uv` y `uv sync --locked`. Si se prefiere no cambiar de herramienta: `pip freeze > pipeline/requirements.txt` desde un entorno que funcione ya es mucho mejor que nada.

---

## 7. Se baja el planeta para leer 25 píxeles

**Qué pasa.** Cada mes de IMERG es un archivo **global** de ~18 MB. Se descarga entero para leer 25 valores (o ≈ 9 000 celdas cuando se haga el promedio por departamento).

**Cómo (dos opciones, ambas verificadas como disponibles para `GPM_3IMERGM` en CMR):**

1. **Harmony** (servicio de NASA): la colección declara `has_spatial_subsetting: true` y `has_variables: true`. Con `harmony-py` se pide solo la caja de Perú y solo `precipitation`. La descarga pasa de 18 MB a unos pocos KB por mes.
2. **Lectura remota**: la colección está en Earthdata Cloud (`cloud_hosted: true`). `earthaccess.open(granulos)` + `xarray.open_mfdataset(..., group="Grid")` lee por rangos HTTP sin guardar el archivo.

> Con el problema 1 (V07 congelado) esto pasa a ser una optimización de una sola vez. Vale la pena solo si se reprocesa a menudo (por ejemplo, al probar el promedio por departamento).

---

## 8. Validar rangos físicos, no solo tipos

**Qué pasa.** `tests/e2e.sh` comprueba que hay 25 regiones y que todo es número. No detecta un error de unidad: olvidar el `× 24` de IMERG (mm/h → mm/día) produce números válidos pero 24 veces más chicos. `docs/guia-pipeline.md` §8 ya avisa de este error.

**Cómo.** Una línea `jq` por archivo:

```bash
chk "gpm.json: lluvia entre 0 y 30 mm/día" \
  jq -e '[.[].anios[].lluvia_mm_dia] | all(. >= 0 and . <= 30)' data/gpm.json
chk "power.json: T2M entre -15 y 35 °C" \
  jq -e '[.[].anios[].T2M] | all(. >= -15 and . <= 35)' data/power.json
```

---

## 9. Menores

| Punto | Por qué | Cómo |
|---|---|---|
| `inicio, fin = (sys.argv[1:3] + [...])[:2]` | Difícil de leer; acepta `"abc"` sin error claro | `argparse` con `type=int`, o dejarlo |
| Lógica de escribir el JSON duplicada en los 2 scripts | `guia-pipeline.md` §7 ya propone `common.py` | Hacerlo **cuando llegue la 3.ª fuente**, no antes |
| `pipeline/exploracion/` (≈ 480 KB de PNG/CSV, usa `geopandas` que no está en `requirements.txt`) | Mezcla exploración con producción | Aceptable en hackathon. Si crece, mover a otro repo o a un *release* |
