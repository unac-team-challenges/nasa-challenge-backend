"""Descarga CHIRPS v2.0 (mensual, ~5 km) de las 25 regiones y escribe data/chirps.json.

Uso: python pipeline/chirps.py [inicio] [fin]   (por defecto 2015 2020)

No necesita cuenta. Lee los GeoTIFF optimizados (COG) del Climate Hazards
Center (UCSB) a distancia: solo baja los píxeles de las capitales.
CHIRPS no es de NASA: sirve como segunda opinión de la lluvia de GPM.
"""
import calendar
import json
import os
import sys
from pathlib import Path

import numpy as np
import rasterio
import requests

from power import REGIONES

# Reintentos de GDAL al leer los COG por HTTP (el servidor a veces falla)
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")

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
        # Año en curso: si diciembre aún no está publicado (404), se omite.
        # Cualquier otro error de red sí debe fallar, no saltarse el año.
        if requests.head(URL.format(anio=anio, mes=12), timeout=60).status_code == 404:
            print(f"{anio}: aún no tiene los 12 meses publicados, se omite", flush=True)
            continue
        meses = [lluvia_mensual(anio, mes) for mes in range(1, 13)]
        # Como power.py, solo años completos: sin sus 12 meses válidos
        # (p. ej. píxel de mar), la región no tiene ese año. Nunca NaN.
        for reg in REGIONES:
            valores = [m[reg] for m in meses if np.isfinite(m[reg])]
            if len(valores) == 12:
                datos[reg][str(anio)] = {"lluvia_mm_dia": round(float(np.mean(valores)), 4)}
        print(f"{anio} listo", flush=True)

    out = [
        {"region": reg, "lat": lat, "lon": lon, "anios": datos[reg]}
        for reg, (lat, lon) in REGIONES.items()
    ]
    Path(__file__).parent.parent.joinpath("data", "chirps.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8"
    )
    print(f"{len(out)} regiones -> data/chirps.json")
