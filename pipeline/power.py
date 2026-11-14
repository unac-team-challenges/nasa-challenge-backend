"""Descarga NASA POWER (mensual) de las 25 regiones y escribe data/power.json.

Uso: python pipeline/power.py [inicio] [fin]   (por defecto 2015 2020)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# Capital de cada región (lat, lon)
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


def anual(lat, lon, inicio, fin):
    r = requests.get(
        "https://power.larc.nasa.gov/api/temporal/monthly/point",
        params={"parameters": "PRECTOTCORR,T2M", "community": "AG",
                "latitude": lat, "longitude": lon,
                "start": inicio, "end": fin, "format": "JSON"},
        timeout=60,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json()["properties"]["parameter"])  # índice = YYYYMM
    df = df[~df.index.str.endswith("13")]  # 13 = promedio anual
    df = df.replace(-999, np.nan).dropna()  # -999 = sin dato
    g = df.groupby(df.index.str[:4])
    return g.mean()[g.size() == 12]  # solo años completos: nunca NaN ni promedios sesgados


if __name__ == "__main__":
    inicio, fin = (sys.argv[1:3] + ["2015", "2020"][len(sys.argv[1:3]):])[:2]
    out = [
        {"region": reg, "lat": lat, "lon": lon,
         "anios": anual(lat, lon, inicio, fin).round(4).to_dict("index")}
        for reg, (lat, lon) in REGIONES.items()
    ]
    Path(__file__).parent.parent.joinpath("data", "power.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8"
    )
    print(f"{len(out)} regiones -> data/power.json")
