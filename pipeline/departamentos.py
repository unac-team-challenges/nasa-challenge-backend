"""Promedio por departamento: máscara de las 25 regiones sobre una malla lat/lon.

GeoJSON: pipeline/geo/peru_departamentos.geojson (juaneladio/peru-geojson,
MPL-2.0). Una celda pertenece al departamento que contiene su centro, igual
que en pipeline/exploracion/lab4_departamentos.py.
"""
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import regionmask

from power import REGIONES

GEOJSON = Path(__file__).parent / "geo" / "peru_departamentos.geojson"
PERU = {"oeste": -81.5, "sur": -18.5, "este": -68.5, "norte": 0.1}  # recuadro aproximado


def _clave(nombre):
    """'Áncash' y 'ANCASH' -> 'ANCASH'."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return sin_tildes.upper()


def _regiones():
    gdf = gpd.read_file(GEOJSON)
    por_clave = {_clave(n): i for i, n in enumerate(gdf["NOMBDEP"])}
    faltan = [r for r in REGIONES if _clave(r) not in por_clave]
    if faltan:
        raise ValueError(f"Sin polígono en el GeoJSON: {faltan}")
    # números de la máscara = posición de la región en REGIONES
    gdf = gdf.iloc[[por_clave[_clave(r)] for r in REGIONES]].reset_index(drop=True)
    ubigeos = dict(zip(REGIONES, gdf["FIRST_IDDP"]))
    return regionmask.from_geopandas(gdf), ubigeos


_REGIONES, UBIGEO = _regiones()  # UBIGEO: {"Amazonas": "01", ...} (texto de 2 dígitos)


def mascara(lat, lon):
    """Matriz (lat, lon) con el índice de la región de REGIONES en cada celda, o NaN."""
    return _REGIONES.mask(np.asarray(lon), np.asarray(lat)).values


def promedios(valores, masc):
    """{region: (promedio, celdas)} de una matriz (lat, lon); ignora NaN."""
    salida = {}
    for i, reg in enumerate(REGIONES):
        celdas = valores[masc == i]
        celdas = celdas[np.isfinite(celdas)]
        salida[reg] = (float(celdas.mean()) if celdas.size else np.nan, int(celdas.size))
    return salida


MIN_CELDAS = 4  # mismo umbral que Josue (pocos_datos)


def a_json(datos, celdas, notas=None):
    """Lista para data/*.json: forma de power.json + `celdas` y, si hace falta, `nota`."""
    notas = notas or {}
    out = []
    for reg, (lat, lon) in REGIONES.items():
        fila = {"region": reg, "lat": lat, "lon": lon, "celdas": celdas.get(reg, 0)}
        if reg in notas:
            fila["nota"] = notas[reg]
        elif fila["celdas"] < MIN_CELDAS:
            fila["nota"] = f"Promedio de solo {fila['celdas']} celda(s): dato poco confiable"
        fila["anios"] = datos[reg]
        out.append(fila)
    return out
