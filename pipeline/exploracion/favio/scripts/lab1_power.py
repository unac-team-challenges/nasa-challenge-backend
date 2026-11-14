"""Laboratorio 1: NASA POWER (sin cuenta). Responde las preguntas de la guía 12."""
import json, os, sys, time, glob
import requests, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
SAL = os.path.join(os.path.dirname(__file__), "salida")
URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
def pedir(lat, lon, params, ini=1981, fin=2024):
    t = time.time()
    r = requests.get(URL, params=dict(parameters=params, community="AG", latitude=lat, longitude=lon, start=ini, end=fin, format="JSON"), timeout=120)
    return r, time.time() - t
# 1-3) variables, unidades y -999 (Piura, como la guía)
r, dt = pedir(-5.19, -80.63, "T2M,PRECTOTCORR,GWETTOP")
d = r.json(); P = d["properties"]["parameter"]
print("HTTP", r.status_code, f"| {dt:.1f} s | variables:", list(P))
for k, v in d["parameters"].items(): print(f"  {k}: {v['longname']} [{v['units']}]")
print("  fuente:", d["header"].get("sources"), "| fill_value:", d["header"].get("fill_value"))
for k in P: print(f"  -999 en {k}:", sum(1 for x in P[k].values() if x == -999))
# 5) humedad
r2, dt2 = pedir(-5.19, -80.63, "RH2M,QV2M,T2MDEW")
print("Humedad: HTTP", r2.status_code, "| aceptados:", list(r2.json().get("properties", {}).get("parameter", {})), r2.json().get("messages"))
# 4) Caso 1: Piura y Tumbes frente a Puno
pts = {"Piura": (-5.19, -80.63), "Tumbes": (-3.57, -80.45), "Puno": (-15.84, -70.02)}
fig, ax = plt.subplots(figsize=(10, 4.2)); tabla = {}
for n, (la, lo) in pts.items():
    s = pd.Series(pedir(la, lo, "PRECTOTCORR")[0].json()["properties"]["parameter"]["PRECTOTCORR"])
    s = s[~s.index.str.endswith("13")].astype(float).replace(-999, float("nan")); s.index = pd.to_datetime(s.index, format="%Y%m")
    anual = s.groupby(s.index.year).mean() * 365; tabla[n] = anual
    ax.plot(anual.index, anual.values, label=n, lw=2)
df = pd.DataFrame(tabla); df.to_csv(os.path.join(SAL, "power_caso1_anual.csv"), float_format="%.0f")
for y in (1983, 1998, 2017, 2023): ax.axvline(y, color="grey", ls=":", lw=1)
ax.set_ylabel("Lluvia anual (mm/año)"); ax.set_title("NASA POWER, lluvia anual 1981–2024 (líneas: años de El Niño)"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(SAL, "power_caso1.png"), dpi=120)
print("\nLluvia anual (mm) en años clave:"); print(df.loc[[1983, 1997, 1998, 2016, 2017, 2022, 2023, 2024]].round(0).to_string())
print("\nPromedio 1981-2024:", df.mean().round(0).to_dict())
# 6) tiempo de 25 consultas (ya hechas en la vista rápida); medimos 3 más
ts = [pedir(-12.05, -77.05, "T2M,PRECTOTCORR,GWETTOP")[1] for _ in range(3)]
print(f"\nTiempo por consulta: {min(ts):.1f}–{max(ts):.1f} s")
