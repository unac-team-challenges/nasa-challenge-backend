"""Laboratorio 3: MODIS MOD13A3 (NDVI) vía la API de AppEEARS.

Uso:
  python lab3_appeears.py enviar   -> crea la solicitud de área y guarda el task_id
  python lab3_appeears.py estado   -> consulta el estado
  python lab3_appeears.py bajar    -> descarga los resultados a labs/data/ndvi

Las credenciales salen del archivo netrc que creó el Laboratorio 0 (earthaccess).
El script nunca las imprime.
"""
import json, os, sys, netrc
import requests

BASE = "https://appeears.earthdatacloud.nasa.gov/api"
AQUI = os.path.dirname(os.path.abspath(__file__))
TASK_FILE = os.path.join(AQUI, "data", "lab3_task.json")
OUT = os.path.join(AQUI, "data", "ndvi")


def credenciales():
    home = os.path.expanduser("~")
    for nombre in ("_netrc", ".netrc"):
        ruta = os.path.join(home, nombre)
        if os.path.exists(ruta):
            a = netrc.netrc(ruta).authenticators("urs.earthdata.nasa.gov")
            if a:
                return a[0], a[2]
    sys.exit("No encontré la sesión de Earthdata. Corre primero lab0_login.py.")


def token():
    r = requests.post(f"{BASE}/login", auth=credenciales(), timeout=60)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def caja(nombre, oeste, sur, este, norte, tipo):
    return {
        "type": "Feature",
        "properties": {"nombre": nombre, "tipo": tipo},
        "geometry": {"type": "Polygon", "coordinates": [[[oeste, sur], [este, sur], [este, norte], [oeste, norte], [oeste, sur]]]},
    }


# Recuadros aproximados (~20 x 20 km). Valles irrigados frente a ciudad, selva y sierra.
ZONAS = [
    caja("Chavimochic (Viru-Chao)", -78.85, -8.60, -78.60, -8.35, "valle irrigado"),
    caja("Olmos", -80.00, -6.10, -79.75, -5.85, "valle irrigado"),
    caja("Ica (valle y Villacuri)", -75.90, -14.15, -75.65, -13.90, "valle irrigado"),
    caja("Lima Metropolitana", -77.10, -12.15, -76.90, -11.90, "ciudad"),
    caja("Selva cerca de Iquitos", -73.70, -4.20, -73.50, -4.00, "selva"),
    caja("Valle del Mantaro (Huancayo)", -75.35, -12.10, -75.15, -11.90, "sierra"),
]


def enviar():
    tarea = {
        "task_type": "area",
        "task_name": "detective-peru-lab3-ndvi",
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
    print("HTTP", r.status_code, r.text[:500])
    r.raise_for_status()
    os.makedirs(os.path.dirname(TASK_FILE), exist_ok=True)
    json.dump(r.json(), open(TASK_FILE, "w"))


def estado():
    tid = json.load(open(TASK_FILE))["task_id"]
    r = requests.get(f"{BASE}/task/{tid}", headers=token(), timeout=60)
    d = r.json()
    print(d.get("status"), "| creada:", d.get("created"), "| actualizada:", d.get("updated"))
    return d.get("status")


def bajar():
    tid = json.load(open(TASK_FILE))["task_id"]
    h = token()
    lista = requests.get(f"{BASE}/bundle/{tid}", headers=h, timeout=60).json()
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for f in lista["files"]:
        dest = os.path.join(OUT, os.path.basename(f["file_name"]))
        with requests.get(f"{BASE}/bundle/{tid}/{f['file_id']}", headers=h, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        total += os.path.getsize(dest)
        print(f"{f['file_name']}  {os.path.getsize(dest)/1e6:.2f} MB")
    print(f"Total: {total/1e6:.1f} MB")


if __name__ == "__main__":
    {"enviar": enviar, "estado": estado, "bajar": bajar}[sys.argv[1]]()
