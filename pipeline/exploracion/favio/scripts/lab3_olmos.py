"""Laboratorio 3b: NDVI de Olmos con el recuadro movido a las tierras irrigadas (MOD13A3 vía AppEEARS).

El recuadro del Lab 3 (-80.00, -6.10, -79.75, -5.85) cayó sobre bosque seco cerca del pueblo de Olmos.
El nuevo recuadro de 0,25° se eligió con un dato independiente del NDVI: es la caja con más campos de
cultivo en OpenStreetMap (landuse=farmland/orchard; ~4.400 polígonos, frente a ~150 en la caja vieja),
consultados con la API Overpass el 2026-11-15. Así el resultado no se elige "mirando la tendencia".

Uso:
  python lab3_olmos.py enviar   -> crea la solicitud y guarda el task_id en data/lab3_olmos_task.json
  python lab3_olmos.py estado   -> consulta el estado (~3 h)
  python lab3_olmos.py bajar    -> descarga el NetCDF a data/ndvi_olmos/
Credenciales: el netrc del Laboratorio 0 (nunca se imprimen).
"""
import json
import os
import sys

import requests

from lab3_appeears import BASE, caja, token

AQUI = os.path.dirname(os.path.abspath(__file__))
TASK_FILE = os.path.join(AQUI, "data", "lab3_olmos_task.json")
OUT = os.path.join(AQUI, "data", "ndvi_olmos")

CAJA_OLMOS = (-80.15, -6.25, -79.90, -6.00)  # (oeste, sur, este, norte): tierras nuevas del Proyecto Olmos
ZONAS = [caja("Olmos (tierras irrigadas)", *CAJA_OLMOS, "valle irrigado")]


def enviar():
    tarea = {
        "task_type": "area",
        "task_name": "detective-peru-lab3-olmos",
        "params": {
            "dates": [{"startDate": "01-01-2001", "endDate": "12-31-2024"}],
            "layers": [
                {"product": "MOD13A3.061", "layer": "_1_km_monthly_NDVI"},
                {"product": "MOD13A3.061", "layer": "_1_km_monthly_pixel_reliability"},
            ],
            "geo": {"type": "FeatureCollection", "features": ZONAS},
            "output": {"format": {"type": "netcdf4"}, "projection": "geographic"},
        },
    }
    r = requests.post(f"{BASE}/task", json=tarea, headers=token(), timeout=120)
    r.raise_for_status()
    os.makedirs(os.path.dirname(TASK_FILE), exist_ok=True)
    json.dump(r.json(), open(TASK_FILE, "w"))
    print("solicitud creada:", r.json()["task_id"])


def _estado(h):
    tid = json.load(open(TASK_FILE))["task_id"]
    r = requests.get(f"{BASE}/task/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    return tid, r.json().get("status")


def estado():
    print(_estado(token())[1])


def bajar():
    h = token()
    tid, st = _estado(h)
    if st != "done":
        sys.exit(f"Aún no termina (estado: {st}).")
    r = requests.get(f"{BASE}/bundle/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    os.makedirs(OUT, exist_ok=True)
    for f in r.json()["files"]:
        if not f["file_name"].endswith(".nc"):
            continue
        destino = os.path.join(OUT, os.path.basename(f["file_name"]))
        with requests.get(f"{BASE}/bundle/{tid}/{f['file_id']}", headers=h, stream=True, timeout=600) as d:
            d.raise_for_status()
            with open(destino, "wb") as fh:
                for trozo in d.iter_content(1 << 20):
                    fh.write(trozo)
        print(os.path.basename(destino), f"{os.path.getsize(destino) / 1e6:.1f} MB")


if __name__ == "__main__":
    {"enviar": enviar, "estado": estado, "bajar": bajar}[sys.argv[1] if len(sys.argv) > 1 else "estado"]()
