"""Lab 1 — NASA POWER (sin cuenta). Solo biblioteca estándar.

Baja la serie mensual 1981–2024 de los 5 puntos de la guía 12 y guarda:
  salida/lab1_power_mensual.csv   (punto, variable, AAAAMM, valor)
  salida/lab1_power_anual.csv     (punto, variable, año, media anual; solo años con 12 meses)
  salida/lab1_power_resumen.json  (tiempos, faltantes, unidades, años pico de lluvia)

Uso:  python3 scripts/lab1_power.py
"""
import csv
import json
import statistics as st
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,GWETTOP,RH2M,QV2M"
INICIO, FIN = 1981, 2024
PUNTOS = {  # guía 12, sección 2
    "Piura": (-5.19, -80.63),
    "Tumbes": (-3.57, -80.45),
    "Puno": (-15.84, -70.02),
    "Lima": (-12.05, -77.05),
    "Iquitos": (-3.75, -73.25),
}
SALIDA = Path(__file__).resolve().parent.parent / "salida"


def pedir(lat, lon):
    q = urllib.parse.urlencode({
        "parameters": PARAMS, "community": "AG", "latitude": lat, "longitude": lon,
        "start": INICIO, "end": FIN, "format": "JSON",
    })
    t = time.time()
    with urllib.request.urlopen(f"{URL}?{q}", timeout=120) as r:
        datos = json.load(r)
    return datos, time.time() - t


def main():
    SALIDA.mkdir(exist_ok=True)
    mensual, anual, resumen = [], [], {"periodo": [INICIO, FIN], "parametros": PARAMS, "puntos": {}}
    for nombre, (lat, lon) in PUNTOS.items():
        datos, seg = pedir(lat, lon)
        par = datos["properties"]["parameter"]
        resumen["unidades"] = {k: v.get("units") for k, v in datos.get("parameters", {}).items()}
        info = {"lat": lat, "lon": lon, "segundos": round(seg, 2), "variables": sorted(par), "faltantes_-999": {}}
        for var, serie in par.items():
            meses = {k: v for k, v in serie.items() if not k.endswith("13")}  # mes 13 = promedio anual
            info["faltantes_-999"][var] = sum(1 for v in meses.values() if v == -999)
            info["n_meses"] = len(meses)
            for k, v in sorted(meses.items()):
                mensual.append([nombre, var, k, "" if v == -999 else v])
            for año in range(INICIO, FIN + 1):
                vals = [meses.get(f"{año}{m:02d}", -999) for m in range(1, 13)]
                if all(v != -999 for v in vals):
                    anual.append([nombre, var, año, round(st.mean(vals), 4)])
        lluvia = {a: v for p, var, a, v in anual if p == nombre and var == "PRECTOTCORR"}
        info["lluvia_media_mm_dia"] = round(st.mean(lluvia.values()), 3)
        info["lluvia_años_pico"] = sorted(lluvia, key=lluvia.get, reverse=True)[:3]
        info["lluvia_marzo_2017_mm_dia"] = par["PRECTOTCORR"].get("201703")
        resumen["puntos"][nombre] = info
        print(f"{nombre}: {seg:.1f}s, picos de lluvia {info['lluvia_años_pico']}")

    with open(SALIDA / "lab1_power_mensual.csv", "w", newline="") as f:
        csv.writer(f).writerows([["punto", "variable", "aaaamm", "valor"], *mensual])
    with open(SALIDA / "lab1_power_anual.csv", "w", newline="") as f:
        csv.writer(f).writerows([["punto", "variable", "anio", "media_anual"], *anual])
    (SALIDA / "lab1_power_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2))
    print("Unidades:", resumen["unidades"])


if __name__ == "__main__":
    main()
