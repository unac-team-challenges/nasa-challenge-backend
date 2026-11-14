# Lab 0 + Lab 2 — IMERG y GPCP con `earthaccess`

**Estado:** ⛔ **bloqueado.** El entorno está instalado, pero la cuenta de Earthdata devuelve:

```
Authentication with Earthdata Login failed with:
{"error":"invalid_credentials","error_description":"Invalid user credentials"}
```

AppEEARS (`POST /api/login`) también falla. **Qué revisar:** que el registro esté terminado (botón *Register*), que el correo esté verificado y que la contraseña de `~/.netrc` sea la vigente. Después:

```bash
cd pipeline/exploracion/josue && .venv/bin/python scripts/lab2_imerg_gpcp.py
```

## Lo que sí se verificó (catálogo CMR, sin cuenta)

| | IMERG Final mensual | GPCP v3.2 mensual |
|---|---|---|
| `short_name` / versión | `GPM_3IMERGM` / `07` | `GPCPMON` / `3.2` |
| Archivo de NASA | GES DISC | GES DISC |
| Primer mes | 1998-01 | 1983-01 |
| **Último mes** | **2025-09** | **2023-12** |
| Archivos en CMR | 333 | 492 |
| Resolución | 0,1° | 0,5° |
| Variable | `Grid/precipitation` | `sat_gauge_precip` |
| **Unidades** | **mm/hr** | **mm/day** |
| Tamaño por mes | 16,6–18,3 MB | ~6,5 MB |
| Serie completa | ~5,8 GB | ~3,2 GB |

Comprobación: `https://cmr.earthdata.nasa.gov/search/granules.json?short_name=GPM_3IMERGM&version=07&sort_key=-start_date&page_size=1`

## Qué hace el script cuando se desbloquee

1. Lab 0: `earthaccess.login(strategy="netrc")`.
2. Busca y baja marzo de 2017 de cada producto (recuadro de Perú).
3. Abre con `h5netcdf` y, si falla, con `netcdf4` (anota cuál funcionó).
4. Recorta a Perú y reporta dimensiones, unidades (`attrs`), número de NaN y el valor de Piura.
5. Guarda el recorte en `salida/lab2_<producto>_peru_201703.nc`.

## Consecuencias para el plan

- **GPCP termina en 2023:** el periodo largo de lluvia es **1983–2023**.
- **IMERG llega a 2025-09** y en CMR empieza en **1998** (hay que confirmarlo al abrir un archivo de 1998).
- **Unidades:** IMERG × 24 = mm/día, para compararlo con GPCP y POWER.
- **Periodo común IMERG–GPCP:** 1998–2023.
