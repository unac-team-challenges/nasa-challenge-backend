"""Laboratorio 1 (guía 12): NASA POWER para Piura, Tumbes y Puno."""
import json
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests

URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PUNTOS = {"Piura": (-5.19, -80.63), "Tumbes": (-3.57, -80.45), "Puno": (-15.84, -70.02)}


def pedir_power(lat, lon, parametros="T2M,PRECTOTCORR,GWETTOP", inicio=2000, fin=2025):
    params = {"parameters": parametros, "community": "AG", "latitude": lat,
              "longitude": lon, "start": inicio, "end": fin, "format": "JSON"}
    t0 = time.time()
    r = requests.get(URL, params=params, timeout=60)
    return r, time.time() - t0


def a_tabla(datos):
    df = pd.DataFrame(datos["properties"]["parameter"])
    df = df[~df.index.str.endswith("13")]          # quitar el "mes 13" (promedio anual)
    df.index = pd.to_datetime(df.index, format="%Y%m")
    return df.replace(-999, float("nan"))


anuales = {}
for nombre, (lat, lon) in PUNTOS.items():
    r, seg = pedir_power(lat, lon)
    r.raise_for_status()
    df = a_tabla(r.json())
    anual = df.groupby(df.index.year).mean()
    anual.to_csv(f"salida/power_{nombre.lower()}_anual.csv")
    anuales[nombre] = anual
    print(f"{nombre}: {seg:.1f}s, {len(r.content)/1024:.0f} KB, {len(df)} meses, "
          f"faltantes={int(df.isna().sum().sum())}, lluvia media={df['PRECTOTCORR'].mean():.2f} mm/día")

# Gráfico del Caso 1
fig, ax = plt.subplots(figsize=(9, 4))
for nombre, anual in anuales.items():
    anual["PRECTOTCORR"].plot(ax=ax, label=nombre, marker="o", ms=3)
ax.set_ylabel("Lluvia media (mm/día)")
ax.set_title("NASA POWER: lluvia anual 2000-2025")
ax.legend()
fig.tight_layout()
fig.savefig("salida/power_caso1.png", dpi=120)

print("\nAños con más lluvia en Piura:")
print(anuales["Piura"]["PRECTOTCORR"].sort_values(ascending=False).head(4).round(2).to_string())

# Prueba de humedad del aire (pregunta 5 de la guía)
for par in ["RH2M", "QV2M"]:
    r, _ = pedir_power(-5.19, -80.63, parametros=par)
    print(f"\n{par}: HTTP {r.status_code}", "OK" if r.ok else r.text[:200])
    if r.ok:
        print("  unidades:", r.json()["parameters"][par]["units"])

# Pregunta 6: 25 consultas seguidas (simulado con 25 puntos dentro de Perú)
t0 = time.time()
errores = 0
for i in range(25):
    r, _ = pedir_power(-5 - i * 0.5, -78, parametros="PRECTOTCORR")
    errores += not r.ok
print(f"\n25 consultas seguidas: {time.time()-t0:.1f}s, errores={errores}")
