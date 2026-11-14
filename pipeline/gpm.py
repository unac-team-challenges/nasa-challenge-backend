"""Descarga GPM IMERG (mensual, V07) de las 25 regiones y escribe data/gpm.json.

Uso: python pipeline/gpm.py [inicio] [fin]   (por defecto 2000 2025)

Necesita una cuenta Earthdata con los términos de GES DISC aceptados:
variables EARTHDATA_USERNAME y EARTHDATA_PASSWORD (en .env o en el
entorno) o un ~/.netrc. Baja un mes a la vez (~18 MB), lo lee y lo
borra: 6 años tardan unos 20-30 minutos.
"""
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import earthaccess
import numpy as np
import requests
import xarray as xr
from dotenv import load_dotenv

from power import REGIONES

MM_HORA_A_MM_DIA = 24  # IMERG viene en mm/hr


def lluvia_mensual(archivo):
    """Lluvia (mm/día) en la celda más cercana a la capital de cada región."""
    # decode_times=False: el eje de tiempo usa calendario juliano y no hace falta
    with xr.open_dataset(archivo, group="Grid", engine="h5netcdf", decode_times=False) as ds:
        lluvia = ds["precipitation"].isel(time=0)
        return {
            reg: float(lluvia.sel(lat=lat, lon=lon, method="nearest")) * MM_HORA_A_MM_DIA
            for reg, (lat, lon) in REGIONES.items()
        }


def descargar(sesion, url, destino, intentos=3):
    """Baja un archivo (un mes, ~18 MB). Reintenta si GES DISC falla o se cuelga."""
    for intento in range(1, intentos + 1):
        try:
            with sesion.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(destino, "wb") as f:
                    for trozo in r.iter_content(1 << 20):
                        f.write(trozo)
            return
        except requests.RequestException:
            if intento == intentos:
                raise
            time.sleep(5 * intento)


def anio_promedio(anio, sesion, carpeta):
    """{region: promedio del año (mm/día)}, un mes a la vez.

    Como power.py, solo años completos: una región sin sus 12 meses
    válidos no tiene ese año (nunca NaN ni promedios sesgados).
    """
    granulos = earthaccess.search_data(
        short_name="GPM_3IMERGM", version="07",
        temporal=(f"{anio}-01-01", f"{anio}-12-31"),
    )
    if not granulos:
        return {}
    meses = []
    archivo = Path(carpeta) / "mes.HDF5"
    for granulo in granulos:
        descargar(sesion, granulo.data_links()[0], archivo)
        meses.append(lluvia_mensual(archivo))
        archivo.unlink()
    promedios = {}
    for reg in REGIONES:
        valores = [m[reg] for m in meses if np.isfinite(m[reg])]
        if len(valores) == 12:
            promedios[reg] = round(float(np.mean(valores)), 4)
    return promedios


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2000", "2025"][len(sys.argv[1:3]):])[:2]
    load_dotenv()
    earthaccess.login()  # .env/entorno, o ~/.netrc
    sesion = earthaccess.get_requests_https_session()

    datos = {reg: {} for reg in REGIONES}
    with tempfile.TemporaryDirectory() as carpeta:
        for anio in range(int(inicio), int(fin) + 1):
            for reg, valor in anio_promedio(anio, sesion, carpeta).items():
                datos[reg][str(anio)] = {"lluvia_mm_dia": valor}
            print(f"{anio} listo", flush=True)

    out = [
        {"region": reg, "lat": lat, "lon": lon, "anios": datos[reg]}
        for reg, (lat, lon) in REGIONES.items()
    ]
    Path(__file__).parent.parent.joinpath("data", "gpm.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8"
    )
    print(f"{len(out)} regiones -> data/gpm.json")
