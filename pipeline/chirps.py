"""Descarga CHIRPS v2.0 (mensual, ~5 km) de las 25 regiones y escribe data/chirps.json.

Uso: python pipeline/chirps.py [inicio] [fin]   (por defecto 2015 2020)

No necesita cuenta. Lee los GeoTIFF optimizados (COG) del Climate Hazards
Center (UCSB) a distancia: solo baja los píxeles de las capitales.
CHIRPS no es de NASA: sirve como segunda opinión de la lluvia de GPM.
"""
import calendar
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

from power import REGIONES

URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/cogs/chirps-v2.0.{anio}.{mes:02d}.cog"


def lluvia_mensual(anio, mes):
    """Lluvia (mm/día) en el píxel de la capital de cada región. CHIRPS viene en mm/mes."""
    dias = calendar.monthrange(anio, mes)[1]
    puntos = [(lon, lat) for lat, lon in REGIONES.values()]  # rasterio pide (x, y)
    with rasterio.open("/vsicurl/" + URL.format(anio=anio, mes=mes)) as src:
        valores = [v[0] for v in src.sample(puntos)]
    # -9999 = sin dato (mar)
    return {reg: (v / dias if v >= 0 else np.nan) for reg, v in zip(REGIONES, valores)}


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2015", "2020"][len(sys.argv[1:3]):])[:2]
    datos = {reg: {} for reg in REGIONES}
    for anio in range(int(inicio), int(fin) + 1):
        meses = [lluvia_mensual(anio, mes) for mes in range(1, 13)]
        for reg in REGIONES:
            valor = float(np.nanmean([m[reg] for m in meses]))
            datos[reg][str(anio)] = {"lluvia_mm_dia": round(valor, 4)}
        print(f"{anio} listo", flush=True)

    out = [
        {"region": reg, "lat": lat, "lon": lon, "anios": datos[reg]}
        for reg, (lat, lon) in REGIONES.items()
    ]
    Path(__file__).parent.parent.joinpath("data", "chirps.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"{len(out)} regiones -> data/chirps.json")
