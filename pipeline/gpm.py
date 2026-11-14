"""Descarga GPM IMERG (mensual, V07) de las 25 regiones y escribe data/gpm.json.

Cada valor es el promedio de todas las celdas de IMERG (0,1°) del
departamento (regla 4 de docs/reglas-datos.md), no el píxel de la capital.

Uso: python pipeline/gpm.py [inicio] [fin]   (por defecto 2015 2020)

Necesita una cuenta Earthdata con los términos de GES DISC aceptados:
variables EARTHDATA_USERNAME y EARTHDATA_PASSWORD (en .env o en el
entorno) o un ~/.netrc. Baja un mes a la vez (~18 MB), lo lee y lo
borra: 6 años tardan unos 20-30 minutos.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

import earthaccess
import numpy as np
import requests
import xarray as xr
from dotenv import load_dotenv

from departamentos import PERU, a_json, mascara, promedios
from power import REGIONES

MM_HORA_A_MM_DIA = 24  # IMERG viene en mm/hr


def lluvia_mensual(archivo):
    """{region: (lluvia mm/día, celdas)}: promedio de las celdas de cada departamento."""
    # decode_times=False: el eje de tiempo usa calendario juliano y no hace falta
    with xr.open_dataset(archivo, group="Grid", engine="h5netcdf", decode_times=False) as ds:
        lluvia = (
            ds["precipitation"].isel(time=0)
            .sel(lat=slice(PERU["sur"], PERU["norte"]), lon=slice(PERU["oeste"], PERU["este"]))
            .transpose("lat", "lon")
        )
        masc = mascara(lluvia["lat"], lluvia["lon"])
        return promedios(lluvia.values * MM_HORA_A_MM_DIA, masc)


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
    """({region: promedio del año (mm/día)}, {region: celdas}), un mes a la vez.

    Como power.py, solo años completos: una región sin sus 12 meses
    válidos no tiene ese año (nunca NaN ni promedios sesgados).
    """
    granulos = earthaccess.search_data(
        short_name="GPM_3IMERGM", version="07",
        temporal=(f"{anio}-01-01", f"{anio}-12-31"),
    )
    if not granulos:
        return {}, {}
    meses = []
    archivo = Path(carpeta) / "mes.HDF5"
    for granulo in granulos:
        descargar(sesion, granulo.data_links()[0], archivo)
        meses.append(lluvia_mensual(archivo))
        archivo.unlink()
    anual = {}
    for reg in REGIONES:
        valores = [m[reg][0] for m in meses if np.isfinite(m[reg][0])]
        if len(valores) == 12:
            anual[reg] = round(float(np.mean(valores)), 4)
    return anual, {reg: v[1] for reg, v in meses[0].items()}


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2015", "2020"][len(sys.argv[1:3]):])[:2]
    load_dotenv()
    earthaccess.login()  # .env/entorno, o ~/.netrc
    sesion = earthaccess.get_requests_https_session()

    datos = {reg: {} for reg in REGIONES}
    celdas = {}
    with tempfile.TemporaryDirectory() as carpeta:
        for anio in range(int(inicio), int(fin) + 1):
            anual, celdas_anio = anio_promedio(anio, sesion, carpeta)
            celdas = celdas_anio or celdas
            for reg, valor in anual.items():
                datos[reg][str(anio)] = {"lluvia_mm_dia": valor}
            print(f"{anio} listo", flush=True)

    out = a_json(datos, celdas)
    Path(__file__).parent.parent.joinpath("data", "gpm.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8"
    )
    print(f"{len(out)} regiones -> data/gpm.json")
