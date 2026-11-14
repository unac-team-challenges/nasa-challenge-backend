"""Descarga NASA POWER (mensual) de las 25 regiones y escribe data/power.json.

Uso: python pipeline/power.py [inicio] [fin]   (por defecto 1981 2024)

Cada valor es el promedio de las celdas de POWER (~0,5° × 0,625°, MERRA-2)
del departamento (regla 3b de docs/reglas-datos.md), con la API regional
en 4 recuadros (máximo 10° por lado), como en
pipeline/exploracion/josue/scripts/power_departamentos.py.
Callao no tiene celdas propias: usa la celda de su capital, con `nota`.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# Capital de cada región (lat, lon): punto del mapa y respaldo si no hay celdas
REGIONES = {
    "Amazonas": (-6.23, -77.87), "Áncash": (-9.53, -77.53),
    "Apurímac": (-13.63, -72.88), "Arequipa": (-16.40, -71.54),
    "Ayacucho": (-13.16, -74.22), "Cajamarca": (-7.16, -78.51),
    "Callao": (-12.06, -77.13), "Cusco": (-13.53, -71.97),
    "Huancavelica": (-12.79, -74.98), "Huánuco": (-9.93, -76.24),
    "Ica": (-14.07, -75.73), "Junín": (-12.07, -75.21),
    "La Libertad": (-8.11, -79.03), "Lambayeque": (-6.77, -79.84),
    "Lima": (-12.05, -77.04), "Loreto": (-3.75, -73.25),
    "Madre de Dios": (-12.59, -69.19), "Moquegua": (-17.19, -70.93),
    "Pasco": (-10.68, -76.26), "Piura": (-5.19, -80.63),
    "Puno": (-15.84, -70.02), "San Martín": (-6.03, -76.97),
    "Tacna": (-18.01, -70.25), "Tumbes": (-3.57, -80.45),
    "Ucayali": (-8.38, -74.55),
}

VARIABLES = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN"]
URL = "https://power.larc.nasa.gov/api/temporal/monthly/regional"
# (lat_min, lat_max, lon_min, lon_max): la API regional admite máx. 10° por lado
RECUADROS = [(-9, 0, -81.5, -73), (-9, 0, -73, -68.5),
             (-18.5, -9, -81.5, -73), (-18.5, -9, -73, -68.5)]


def malla(var, inicio, fin):
    """DataFrame (lat, lon, anio, mes, valor) de POWER sobre Perú, sin -999 ni el 'mes 13'."""
    filas = []
    for lat_min, lat_max, lon_min, lon_max in RECUADROS:
        r = requests.get(URL, params={
            "parameters": var, "community": "AG", "format": "JSON",
            "latitude-min": lat_min, "latitude-max": lat_max,
            "longitude-min": lon_min, "longitude-max": lon_max,
            "start": inicio, "end": fin,
        }, timeout=600)
        r.raise_for_status()
        for feat in r.json()["features"]:
            lon, lat = feat["geometry"]["coordinates"][:2]
            for k, v in feat["properties"]["parameter"][var].items():
                if not k.endswith("13") and v != -999:
                    filas.append((lat, lon, int(k[:4]), int(k[4:]), v))
    df = pd.DataFrame(filas, columns=["lat", "lon", "anio", "mes", "valor"])
    return df.drop_duplicates(["lat", "lon", "anio", "mes"])  # bordes compartidos entre recuadros


def por_departamento(df):
    """({region: {anio: media anual}}, {region: celdas}). Solo años con 12 meses."""
    from departamentos import mascara  # aquí: departamentos importa REGIONES de este módulo

    lats, lons = np.unique(df["lat"]), np.unique(df["lon"])
    masc = mascara(lats, lons)
    i_lat = {v: i for i, v in enumerate(lats)}
    i_lon = {v: i for i, v in enumerate(lons)}
    df = df.assign(reg=[masc[i_lat[a], i_lon[o]] for a, o in zip(df["lat"], df["lon"])])

    nombres = list(REGIONES)
    anual, celdas = {}, {}
    for i, reg in enumerate(nombres):
        sub = df[df["reg"] == i]
        celdas[reg] = int(sub[["lat", "lon"]].drop_duplicates().shape[0])
        if sub.empty:  # sin celdas propias (Callao): la celda de la capital
            lat, lon = REGIONES[reg]
            cerca = df.loc[((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2).idxmin(), ["lat", "lon"]]
            sub = df[(df["lat"] == cerca["lat"]) & (df["lon"] == cerca["lon"])]
        mensual = sub.groupby(["anio", "mes"])["valor"].mean()
        n_meses = mensual.groupby(level="anio").size()
        anios_ok = n_meses[n_meses == 12].index
        anual[reg] = mensual[mensual.index.get_level_values("anio").isin(anios_ok)].groupby(level="anio").mean()
    return anual, celdas


if __name__ == "__main__":
    from departamentos import a_json

    inicio, fin = (sys.argv[1:3] + ["1981", "2024"][len(sys.argv[1:3]):])[:2]
    por_var, celdas = {}, {}
    for var in VARIABLES:
        por_var[var], celdas = por_departamento(malla(var, inicio, fin))
        print(f"{var} listo", flush=True)

    datos = {}
    for reg in REGIONES:
        # un año entra solo si las 4 variables lo tienen completo
        anios = set.intersection(*(set(por_var[v][reg].index) for v in VARIABLES))
        datos[reg] = {str(a): {v: round(float(por_var[v][reg][a]), 4) for v in VARIABLES}
                      for a in sorted(anios)}
    notas = {reg: "Sin celdas propias de POWER: se usa la celda de la capital (compartida con Lima)"
             for reg, n in celdas.items() if n == 0}
    Path(__file__).parent.parent.joinpath("data", "power.json").write_text(
        json.dumps(a_json(datos, celdas, notas), ensure_ascii=False, indent=1, allow_nan=False),
        encoding="utf-8",
    )
    print(f"{len(REGIONES)} regiones -> data/power.json")
