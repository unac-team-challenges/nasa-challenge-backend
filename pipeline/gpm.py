"""Descarga GPM IMERG (mensual, V07) de las 25 regiones y escribe data/gpm.json.

Cada valor es el promedio de todas las celdas de IMERG (0,1°) del
departamento (regla 3b de docs/reglas-datos.md), no el píxel de la capital.

Uso: python pipeline/gpm.py [inicio] [fin]   (por defecto 2001 2024)

Necesita una cuenta Earthdata con los términos de GES DISC aceptados:
variables EARTHDATA_USERNAME y EARTHDATA_PASSWORD (en .env o en el
entorno) o un ~/.netrc. Pide a GES DISC por OPeNDAP solo el recorte de
Perú de cada mes (~60 KB en vez del archivo global de ~18 MB), en
memoria: no deja nada en disco. 2001–2024 tarda unos minutos.
"""
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import earthaccess
import numpy as np
import requests
import xarray as xr
from dotenv import load_dotenv

from departamentos import a_json, mascara, promedios
from power import REGIONES

MM_HORA_A_MM_DIA = 24  # IMERG viene en mm/hr
OPENDAP = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGM.07"
# Índices de la malla global de 0,1° (centros en x.x5) que cubren Perú:
# lon -81,45..-68,55 -> 985..1114 ; lat -18,45..0,05 -> 715..900
RECORTE = "/precipitation[0:0][985:1114][715:900];/lat[715:900];/lon[985:1114]"
HILOS = 4


def url_recorte(granulo):
    """URL OPeNDAP (DAP4 -> netCDF4) del recorte de Perú de un granulo."""
    https = granulo.data_links()[0]  # .../GPM_3IMERGM.07/2017/3B-MO....HDF5
    anio, nombre = https.split("/")[-2:]
    return f"{OPENDAP}/{anio}/{nombre}.dap.nc4"


def pedir(sesion, url, intentos=3):
    """Bytes del recorte. Reintenta si GES DISC falla o se cuelga."""
    for intento in range(1, intentos + 1):
        try:
            r = sesion.get(url, params={"dap4.ce": RECORTE}, timeout=120)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if intento == intentos:
                raise
            time.sleep(5 * intento)


def lluvia_mensual(contenido):
    """{region: (lluvia mm/día, celdas)}: promedio de las celdas de cada departamento."""
    # decode_times=False: el eje de tiempo usa calendario juliano y no hace falta
    with xr.open_dataset(io.BytesIO(contenido), engine="h5netcdf", decode_times=False) as ds:
        lluvia = ds["precipitation"].isel(time=0).transpose("lat", "lon")
        return promedios(lluvia.values * MM_HORA_A_MM_DIA, mascara(lluvia["lat"], lluvia["lon"]))


def anio_promedio(anio, sesion):
    """({region: promedio del año (mm/día)}, {region: celdas}).

    Como power.py, solo años completos: una región sin sus 12 meses
    válidos no tiene ese año (nunca NaN ni promedios sesgados).
    """
    granulos = earthaccess.search_data(
        short_name="GPM_3IMERGM", version="07",
        temporal=(f"{anio}-01-01", f"{anio}-12-31"),
    )
    if not granulos:
        return {}, {}
    with ThreadPoolExecutor(HILOS) as hilos:
        contenidos = list(hilos.map(lambda g: pedir(sesion, url_recorte(g)), granulos))
    meses = [lluvia_mensual(c) for c in contenidos]
    anual = {}
    for reg in REGIONES:
        valores = [m[reg][0] for m in meses if np.isfinite(m[reg][0])]
        if len(valores) == 12:
            anual[reg] = round(float(np.mean(valores)), 4)
    return anual, {reg: v[1] for reg, v in meses[0].items()}


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2001", "2024"][len(sys.argv[1:3]):])[:2]
    load_dotenv()
    earthaccess.login()  # .env/entorno, o ~/.netrc
    sesion = earthaccess.get_requests_https_session()

    datos = {reg: {} for reg in REGIONES}
    celdas = {}
    for anio in range(int(inicio), int(fin) + 1):
        anual, celdas_anio = anio_promedio(anio, sesion)
        celdas = celdas_anio or celdas
        for reg, valor in anual.items():
            datos[reg][str(anio)] = {"lluvia_mm_dia": valor}
        print(f"{anio} listo", flush=True)

    Path(__file__).parent.parent.joinpath("data", "gpm.json").write_text(
        json.dumps(a_json(datos, celdas), ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print(f"{len(REGIONES)} regiones -> data/gpm.json")
