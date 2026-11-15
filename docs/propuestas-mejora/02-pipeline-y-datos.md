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
- El cron mensual bajaría **≈ 27 años × 12 meses × 18 MB ≈ 5,8 GB** cada mes para obtener exactamente el mismo resultado.
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

## 7. Se baja el planeta para leer 25 píxeles

**Qué pasa.** Cada mes de IMERG es un archivo **global** de ~18 MB. Se descarga entero para leer 25 valores (o ≈ 9 000 celdas cuando se haga el promedio por departamento).

**Cómo (dos opciones, ambas verificadas como disponibles para `GPM_3IMERGM` en CMR):**

1. **Harmony** (servicio de NASA): la colección declara `has_spatial_subsetting: true` y `has_variables: true`. Con `harmony-py` se pide solo la caja de Perú y solo `precipitation`. La descarga pasa de 18 MB a unos pocos KB por mes.
2. **Lectura remota**: la colección está en Earthdata Cloud (`cloud_hosted: true`). `earthaccess.open(granulos)` + `xarray.open_mfdataset(..., group="Grid")` lee por rangos HTTP sin guardar el archivo.

> Con el problema 1 (V07 congelado) esto pasa a ser una optimización de una sola vez. Vale la pena solo si se reprocesa a menudo (por ejemplo, al probar el promedio por departamento).

---

## 9. Menores

| Punto | Por qué | Cómo |
|---|---|---|
| `inicio, fin = (sys.argv[1:3] + [...])[:2]` | Difícil de leer; acepta `"abc"` sin error claro | `argparse` con `type=int`, o dejarlo |
| Lógica de escribir el JSON duplicada en los 2 scripts | `guia-pipeline.md` §7 ya propone `common.py` | Hacerlo **cuando llegue la 3.ª fuente**, no antes |
| `pipeline/exploracion/` (≈ 480 KB de PNG/CSV) | Mezcla exploración con producción | Aceptable en hackathon. Si crece, mover a otro repo o a un *release* |
