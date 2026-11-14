"""Lab 4 — GeoJSON de departamentos: ¿cuántas celdas de cada dataset caen en cada uno?

Cuenta los centros de celda dentro de cada polígono (ray casting, con huecos y
MultiPolygon). Mallas usadas, verificadas el 14 nov 2026:
  IMERG  GPM_3IMERGM v07   0.1°           centros en x.x5 (CMR)
  GPCP   GPCPMON v3.2      0.5°           centros en x.25 / x.75 (CMR)
  POWER  (MERRA-2)         0.5° x 0.625°  centros lat en x.0/x.5, lon = -180 + k*0.625
                                          (comprobado con la respuesta regional de la API)

Solo biblioteca estándar. Entrada: data/peru_departamental_simple.geojson
(juaneladio/peru-geojson). Salida: salida/lab4_celdas_departamento.csv

Uso:  python3 scripts/lab4_celdas_departamento.py
"""
import csv
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GEOJSON = RAIZ / "data" / "peru_departamental_simple.geojson"
UMBRAL_POCOS = 4  # propuesta: menos de 4 celdas = pocos_datos (decisión pendiente de Josue)


def malla(paso_lat, paso_lon, lat0, lon0, bbox):
    oeste, sur, este, norte = bbox
    i0, i1 = math.floor((sur - lat0) / paso_lat), math.ceil((norte - lat0) / paso_lat)
    j0, j1 = math.floor((oeste - lon0) / paso_lon), math.ceil((este - lon0) / paso_lon)
    return [(lon0 + j * paso_lon, lat0 + i * paso_lat) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)]


MALLAS = {  # (paso_lat, paso_lon, origen_lat, origen_lon) del centro de celda
    "IMERG_0.1": (0.1, 0.1, -89.95, -179.95),
    "GPCP_0.5": (0.5, 0.5, -89.75, -179.75),
    "POWER_0.5x0.625": (0.5, 0.625, -90.0, -180.0),
}


def en_anillo(x, y, anillo):
    dentro = False
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            dentro = not dentro
    return dentro


def en_geometria(x, y, geom):
    polis = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for exterior, *huecos in polis:
        if en_anillo(x, y, exterior) and not any(en_anillo(x, y, h) for h in huecos):
            return True
    return False


def bbox_geom(geom):
    polis = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    pts = [p for poli in polis for p in poli[0]]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def autoprueba():
    cuadrado = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                                                    [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]]]}
    assert en_geometria(0.2, 0.2, cuadrado) and not en_geometria(0.5, 0.5, cuadrado)
    assert not en_geometria(1.5, 0.5, cuadrado)
    assert len([p for p in malla(0.1, 0.1, -89.95, -179.95, (0, 0, 1, 1)) if en_geometria(*p, cuadrado)]) == 96
    print("autoprueba OK")


def main():
    autoprueba()
    feats = json.loads(GEOJSON.read_text())["features"]
    filas = []
    for f in feats:
        p, g = f["properties"], f["geometry"]
        bb = bbox_geom(g)
        fila = {"ubigeo": p["FIRST_IDDP"], "departamento": p["NOMBDEP"],
                "area_km2": round(p["HECTARES"] / 100), "ubigeo_es_texto": isinstance(p["FIRST_IDDP"], str)}
        for nombre, (dlat, dlon, lat0, lon0) in MALLAS.items():
            fila[nombre] = sum(en_geometria(x, y, g) for x, y in malla(dlat, dlon, lat0, lon0, bb))
        fila["MODIS_1km_aprox"] = fila["area_km2"]  # 1 celda ≈ 1 km²
        fila["pocos_datos"] = ",".join(k for k in MALLAS if fila[k] < UMBRAL_POCOS) or "-"
        filas.append(fila)
    filas.sort(key=lambda r: r["IMERG_0.1"])
    salida = RAIZ / "salida" / "lab4_celdas_departamento.csv"
    with open(salida, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    for r in filas:
        print(f"{r['ubigeo']} {r['departamento']:15} {r['area_km2']:>7} km²  IMERG={r['IMERG_0.1']:>5} "
              f"GPCP={r['GPCP_0.5']:>4} POWER={r['POWER_0.5x0.625']:>4}  pocos_datos: {r['pocos_datos']}")
    print("ubigeo como texto en todos:", all(r["ubigeo_es_texto"] for r in filas), "| departamentos:", len(filas))


if __name__ == "__main__":
    main()
