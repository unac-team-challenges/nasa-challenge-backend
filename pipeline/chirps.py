"""Descarga CHIRPS v2.0 (mensual, ~5 km) de las 25 regiones y escribe data/chirps.json.

Uso: python pipeline/chirps.py [inicio] [fin]   (por defecto 2015 2020)

Cada valor es el promedio de todos los píxeles de CHIRPS (0,05°) del
departamento (regla 4 de docs/reglas-datos.md), no el píxel de la capital.
No necesita cuenta. Lee los GeoTIFF optimizados (COG) del Climate Hazards
Center (UCSB) a distancia: solo baja la ventana de Perú.
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
from rasterio.windows import from_bounds

from departamentos import PERU, a_json, mascara, promedios
from power import REGIONES

# Reintentos de GDAL al leer los COG por HTTP (el servidor a veces falla)
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")

URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/cogs/chirps-v2.0.{anio}.{mes:02d}.cog"


def lluvia_mensual(anio, mes):
    """{region: (lluvia mm/día, píxeles)}. CHIRPS viene en mm/mes; -9999 (mar) se ignora."""
    with rasterio.open("/vsicurl/" + URL.format(anio=anio, mes=mes)) as src:
        ventana = from_bounds(PERU["oeste"], PERU["sur"], PERU["este"], PERU["norte"], src.transform)
        valores = src.read(1, window=ventana).astype(float)
        transform = src.window_transform(ventana)
    filas, cols = valores.shape
    # centros de píxel: lat baja de norte a sur en un GeoTIFF
    lon = transform.c + transform.a * (np.arange(cols) + 0.5)
    lat = transform.f + transform.e * (np.arange(filas) + 0.5)
    valores[valores < 0] = np.nan
    valores /= calendar.monthrange(anio, mes)[1]
    return promedios(valores, mascara(lat, lon))


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2015", "2020"][len(sys.argv[1:3]):])[:2]
    datos = {reg: {} for reg in REGIONES}
    celdas = {}
    for anio in range(int(inicio), int(fin) + 1):
        # Año en curso: si diciembre aún no está publicado (404), se omite.
        # Cualquier otro error de red sí debe fallar, no saltarse el año.
        if requests.head(URL.format(anio=anio, mes=12), timeout=60).status_code == 404:
            print(f"{anio}: aún no tiene los 12 meses publicados, se omite", flush=True)
            continue
        meses = [lluvia_mensual(anio, mes) for mes in range(1, 13)]
        celdas = {reg: v[1] for reg, v in meses[0].items()}
        # Como power.py, solo años completos: sin sus 12 meses válidos
        # la región no tiene ese año. Nunca NaN.
        for reg in REGIONES:
            valores = [m[reg][0] for m in meses if np.isfinite(m[reg][0])]
            if len(valores) == 12:
                datos[reg][str(anio)] = {"lluvia_mm_dia": round(float(np.mean(valores)), 4)}
        print(f"{anio} listo", flush=True)

    Path(__file__).parent.parent.joinpath("data", "chirps.json").write_text(
        json.dumps(a_json(datos, celdas), ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print(f"{len(REGIONES)} regiones -> data/chirps.json")
