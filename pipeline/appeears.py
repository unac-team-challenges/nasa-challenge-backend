"""Cliente de AppEEARS (NASA LP DAAC) compartido por ndvi.py y cobertura.py.

Cada pipeline dice qué producto, capas, zonas y años pide; aquí está lo común: credenciales, token,
crear la solicitud, consultar su estado, bajar los NetCDF y encontrar el NetCDF de cada zona. Un
arreglo (paginado, reintentos...) se hace una sola vez aquí.

Credenciales: EARTHDATA_USERNAME y EARTHDATA_PASSWORD del entorno (.env local o secrets de GitHub);
si no están, ~/.netrc o ~/_netrc en Windows (el que crea earthaccess). Nunca se imprimen.
"""
import json
import netrc
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
API = "https://appeears.earthdatacloud.nasa.gov/api"


def credenciales():
    try:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env")
    except ImportError:
        pass
    usuario, clave = os.environ.get("EARTHDATA_USERNAME"), os.environ.get("EARTHDATA_PASSWORD")
    if usuario and clave:
        return usuario, clave
    for nombre in (".netrc", "_netrc"):  # en Windows, earthaccess lo guarda como _netrc
        ruta = Path.home() / nombre
        if ruta.exists() and (a := netrc.netrc(ruta).authenticators("urs.earthdata.nasa.gov")):
            return a[0], a[2]
    sys.exit("Faltan EARTHDATA_USERNAME y EARTHDATA_PASSWORD (ver .env.example) o ~/.netrc.")


def token():
    import requests
    r = requests.post(f"{API}/login", auth=credenciales(), timeout=60)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def enviar(zonas, producto, capas, anios, task, nombre):
    """Crea una solicitud de área (un polígono por zona, NetCDF en proyección geográfica) y guarda
    la respuesta (con el task_id) en `task`. `zonas`: las tuplas de ZONAS de ndvi.py y
    cobertura.py: el índice 0 es el id y el 5 la caja (oeste, sur, este, norte)."""
    import requests
    feats = [{"type": "Feature", "properties": {"id": z[0]},
              "geometry": {"type": "Polygon", "coordinates": [[[o, s], [e, s], [e, n], [o, n], [o, s]]]}}
             for z in zonas for (o, s, e, n) in [z[5]]]
    tarea = {"task_type": "area", "task_name": nombre,
             "params": {"dates": [{"startDate": f"01-01-{anios[0]}", "endDate": f"12-31-{anios[-1]}"}],
                        "layers": [{"product": producto, "layer": c} for c in capas],
                        "geo": {"type": "FeatureCollection", "features": feats},
                        "output": {"format": {"type": "netcdf4"}, "projection": "geographic"}}}
    r = requests.post(f"{API}/task", json=tarea, headers=token(), timeout=120)
    r.raise_for_status()
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text(json.dumps(r.json()))
    print("solicitud creada:", r.json()["task_id"])


def estado(h, task):
    import requests
    tid = json.loads(task.read_text())["task_id"]
    r = requests.get(f"{API}/task/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    return tid, r.json().get("status")


def consultar(task):
    print(estado(token(), task)[1])


def bajar(task, destino_dir):
    """Descarga los NetCDF de la solicitud a `destino_dir`.

    Se baja todo a .part y solo al final se reemplazan los .nc: si la descarga se corta, la copia
    buena anterior sigue ahí (repetir la solicitud a AppEEARS cuesta horas).
    """
    import requests
    destino_dir.mkdir(parents=True, exist_ok=True)
    h = token()
    tid, est = estado(h, task)
    if est != "done":
        sys.exit(f"La solicitud aún no termina (estado: {est}). Prueba más tarde con `estado`.")
    r = requests.get(f"{API}/bundle/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    for viejo in destino_dir.glob("*.part"):  # restos de una corrida que murió sin poder limpiar
        viejo.unlink()
    nuevos = []
    parcial = None  # el .part que se está escribiendo (se limpia también si falla a medias)
    try:
        for f in r.json()["files"]:
            if not f["file_name"].endswith(".nc"):
                continue
            destino = destino_dir / Path(f["file_name"]).name
            parcial = destino.with_name(destino.name + ".part")
            with requests.get(f"{API}/bundle/{tid}/{f['file_id']}", headers=h, stream=True,
                              timeout=600) as d:
                d.raise_for_status()
                with open(parcial, "wb") as fh:
                    for trozo in d.iter_content(1 << 20):
                        fh.write(trozo)
            nuevos.append((parcial, destino))
            print(destino.name, f"{parcial.stat().st_size / 1e6:.1f} MB")
            parcial = None
    except BaseException:
        for p in [*(p for p, _ in nuevos), parcial]:
            if p is not None:
                p.unlink(missing_ok=True)
        raise
    if not nuevos:
        # Sin ningún .nc en el bundle no se toca la caché: la copia buena anterior sigue
        sys.exit("El bundle de AppEEARS no trae ningún .nc; se conserva la copia anterior.")
    finales = {d for _, d in nuevos}
    for viejo in destino_dir.glob("*.nc"):  # sin NetCDF de solicitudes anteriores
        if viejo not in finales:
            viejo.unlink()
    for parcial, destino in nuevos:
        parcial.replace(destino)


def nc_de_zona(cache, zona):
    """El único NetCDF de `cache` cuyo centro cae en la caja de la zona (AppEEARS no lo nombra por id)."""
    import xarray as xr
    o, s, e, n = zona[5]
    candidatos = []
    for ruta in sorted(cache.glob("*.nc")):
        with xr.open_dataset(ruta) as ds:
            if o <= float(ds.lon.mean()) <= e and s <= float(ds.lat.mean()) <= n:
                candidatos.append(ruta)
    if len(candidatos) != 1:
        sys.exit(f"{zona[1]}: {len(candidatos)} NetCDF en {cache} (se espera 1). Corre `bajar` de nuevo.")
    return candidatos[0]
