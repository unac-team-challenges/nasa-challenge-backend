"""Temperatura (y lluvia de POWER como 3.ª opinión) por departamento, 1981–2024.

Pasos:
  1. Baja la malla regional de POWER en 4 recuadros (la API admite máx. 10° por lado).
  2. Asigna cada celda a un departamento con regionmask (centro de celda dentro del polígono).
  3. Promedia las celdas de cada departamento por mes → media anual (años con 12 meses).
  4. Tendencia con el método de lab5 (TFPW + Sen + IC95) y Benjamini-Hochberg entre los 25.
  5. Umbral EXIGENTE (decisión de Josue, 14 nov 2026):
       pocos_datos  : < 4 celdas  o  < 20 años
       real         : q < 0.05  y  IC95 de Sen no incluye 0  y  |lag1| <= 0.5
       posible_casualidad : el resto (se anota el motivo en `motivo`)

Salida: salida/power_departamentos_{anual.csv,tendencias.csv,tendencias.json}
Uso:    .venv/bin/python scripts/power_departamentos.py
"""
import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import regionmask
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab5_tendencias import analizar, bh  # noqa: E402  misma implementación validada en lab5

RAIZ = Path(__file__).resolve().parent.parent
URL = "https://power.larc.nasa.gov/api/temporal/monthly/regional"
RECUADROS = {"NO": (-9, 0, -81.5, -73), "NE": (-9, 0, -73, -68.5),
             "SO": (-18.5, -9, -81.5, -73), "SE": (-18.5, -9, -73, -68.5)}
VARIABLES = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR"]
PERIODOS = {"largo": (1981, 2024), "reciente": (2001, 2024)}
MIN_CELDAS, MIN_AÑOS, MAX_LAG1, ALFA = 4, 20, 0.5, 0.05
CACHE = RAIZ / "data" / "power_regional"


def bajar(var, nombre, caja):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{var}_{nombre}.json"
    if f.exists():
        return json.loads(f.read_text()), 0.0
    smin, smax, wmin, wmax = caja
    t = time.time()
    r = requests.get(URL, params={"parameters": var, "community": "AG", "latitude-min": smin,
                                  "latitude-max": smax, "longitude-min": wmin, "longitude-max": wmax,
                                  "start": 1981, "end": 2024, "format": "JSON"}, timeout=600)
    r.raise_for_status()
    f.write_text(r.text)
    return r.json(), time.time() - t


def a_tabla(datos, var):
    filas = []
    for feat in datos["features"]:
        lon, lat = feat["geometry"]["coordinates"][:2]
        for k, v in feat["properties"]["parameter"][var].items():
            if not k.endswith("13") and v != -999:
                filas.append((lon, lat, int(k[:4]), int(k[4:]), v))
    return pd.DataFrame(filas, columns=["lon", "lat", "anio", "mes", "valor"])


def estado(r, celdas):
    if celdas < MIN_CELDAS or r.get("n_years", 0) < MIN_AÑOS:
        return "pocos_datos", f"celdas={celdas}, años={r.get('n_years')}"
    motivos = []
    if r["q_value"] >= ALFA:
        motivos.append(f"q={r['q_value']:.3f}")
    if r["ci_low"] <= 0 <= r["ci_high"]:
        motivos.append("IC95 incluye 0")
    if abs(r["lag1"]) > MAX_LAG1:
        motivos.append(f"lag1={r['lag1']:.2f}")
    return ("real", "") if not motivos else ("posible_casualidad", "; ".join(motivos))


def main():
    gdf = gpd.read_file(RAIZ / "data" / "peru_departamental_simple.geojson")
    log = {}
    anual_todo, resultados = [], []
    for var in VARIABLES:
        partes = []
        for nombre, caja in RECUADROS.items():
            datos, seg = bajar(var, nombre, caja)
            log[f"{var}_{nombre}"] = round(seg, 1)
            partes.append(a_tabla(datos, var))
        df = pd.concat(partes).drop_duplicates(["lon", "lat", "anio", "mes"])
        celdas = df[["lon", "lat"]].drop_duplicates().reset_index(drop=True)
        mascara = regionmask.mask_geopandas(gdf, np.unique(celdas["lon"]), np.unique(celdas["lat"]), wrap_lon=False)
        # la máscara es una malla lat×lon; se lee el departamento de cada celda
        celdas["dep"] = [mascara.sel(lon=lo, lat=la).item() for lo, la in zip(celdas["lon"], celdas["lat"])]
        df = df.merge(celdas, on=["lon", "lat"])
        df = df[df["dep"].notna()]
        n_celdas = celdas.dropna().groupby("dep").size()
        mensual = df.groupby(["dep", "anio", "mes"])["valor"].mean().reset_index()
        completos = mensual.groupby(["dep", "anio"]).filter(lambda g: len(g) == 12)
        anual = completos.groupby(["dep", "anio"])["valor"].mean().reset_index()
        for i, fila in gdf.iterrows():
            serie_dep = anual[anual["dep"] == i]
            for _, a in serie_dep.iterrows():
                anual_todo.append({"variable": var, "ubigeo": fila["FIRST_IDDP"], "departamento": fila["NOMBDEP"],
                                   "anio": int(a["anio"]), "media_anual": round(a["valor"], 4)})
        for periodo, (ini, fin) in PERIODOS.items():
            bloque = []
            for i, fila in gdf.iterrows():
                s = anual[(anual["dep"] == i) & anual["anio"].between(ini, fin)]
                r = analizar(dict(zip(s["anio"].astype(int), s["valor"])))
                bloque.append({"variable": var, "periodo": periodo, "ubigeo": fila["FIRST_IDDP"],
                               "departamento": fila["NOMBDEP"], "celdas": int(n_celdas.get(i, 0)), **r})
            con_p = [b for b in bloque if "p_value" in b]
            for b, q in zip(con_p, bh([b["p_value"] for b in con_p])):
                b["q_value"] = q
            for b in bloque:
                b["status"], b["motivo"] = estado(b, b["celdas"]) if "q_value" in b else ("pocos_datos", "sin serie")
            resultados += bloque
    pd.DataFrame(anual_todo).to_csv(RAIZ / "salida" / "power_departamentos_anual.csv", index=False)
    cols = ["variable", "periodo", "ubigeo", "departamento", "celdas", "year_start", "year_end", "n_years",
            "slope_per_decade", "ci_low", "ci_high", "pct_change_per_decade", "intercept", "p_value", "q_value",
            "lag1", "status", "motivo"]
    pd.DataFrame(resultados).reindex(columns=cols).to_csv(RAIZ / "salida" / "power_departamentos_tendencias.csv",
                                                           index=False)
    (RAIZ / "salida" / "power_departamentos_tendencias.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=1, default=float))
    print("tiempos de descarga (s):", log)
    res = pd.DataFrame(resultados)
    print(res.groupby(["variable", "periodo", "status"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
