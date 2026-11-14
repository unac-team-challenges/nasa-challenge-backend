"""Lab 0 + Lab 2 — IMERG (y GPCP) con earthaccess. NO PROBADO TODAVÍA.

Falta: (1) instalar earthaccess, xarray, h5netcdf; (2) credencial Earthdata en
~/.netrc o login interactivo. Nunca escribir usuario/clave en este archivo.

Datos verificados en CMR el 14 nov 2026:
  GPM_3IMERGM v07: 1998-01 .. 2025-09, 0.1°, variable Grid/precipitation en mm/hr, ~17 MB/mes
  GPCPMON v3.2:    1983-01 .. 2023-12, 0.5°, variable sat_gauge_precip en mm/day, ~6.5 MB/mes

Uso:  .venv/bin/python scripts/lab2_imerg_gpcp.py
"""
import time
from pathlib import Path

import earthaccess
import xarray as xr

RAIZ = Path(__file__).resolve().parent.parent
BBOX = (-81.5, -18.5, -68.5, 0.1)  # oeste, sur, este, norte (guía 12)
PIURA = (-5.19, -80.63)
PRODUCTOS = {
    "IMERG": {"short_name": "GPM_3IMERGM", "version": "07", "var": "precipitation", "grupo": "Grid"},
    "GPCP": {"short_name": "GPCPMON", "version": "3.2", "var": "sat_gauge_precip", "grupo": None},
}
MES = ("2017-03-01", "2017-03-31")  # El Niño costero


def abrir(ruta, grupo):
    for motor in ("h5netcdf", "netcdf4"):
        try:
            return xr.open_dataset(ruta, engine=motor, group=grupo), motor
        except Exception as e:  # anotar en el registro cuál falló
            print(f"  motor {motor} falló: {e}")
    raise RuntimeError("no se pudo abrir el archivo")


def main():
    auth = earthaccess.login(strategy="netrc")  # o strategy="interactive"
    print("Lab 0 — sesión iniciada:", auth.authenticated)
    for nombre, p in PRODUCTOS.items():
        print(f"\n== {nombre}")
        res = earthaccess.search_data(short_name=p["short_name"], version=p["version"],
                                      bounding_box=BBOX, temporal=MES)
        print("granules:", len(res))
        t = time.time()
        archivos = earthaccess.download(res, str(RAIZ / "data" / nombre.lower()))
        print(f"descarga: {time.time() - t:.1f}s, {Path(archivos[0]).stat().st_size / 1e6:.1f} MB")
        ds, motor = abrir(archivos[0], p["grupo"])
        lluvia = ds[p["var"]]
        print("motor:", motor, "| dims:", lluvia.dims, "| unidades:", lluvia.attrs.get("units"))
        lat = "lat" if "lat" in lluvia.dims else "latitude"
        lon = "lon" if "lon" in lluvia.dims else "longitude"
        peru = lluvia.sel({lon: slice(BBOX[0], BBOX[2]), lat: slice(BBOX[1], BBOX[3])}).squeeze()
        print("celdas Perú:", peru.size, "| NaN:", int(peru.isnull().sum()))
        print("Piura marzo 2017:", float(peru.sel({lat: PIURA[0], lon: PIURA[1]}, method="nearest")),
              lluvia.attrs.get("units"))
        peru.to_netcdf(RAIZ / "salida" / f"lab2_{nombre.lower()}_peru_201703.nc")


if __name__ == "__main__":
    main()
