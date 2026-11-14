"""Laboratorio 3: análisis del NDVI (MODIS MOD13A3) de 6 zonas, 2001–2024.

Entrada: scripts/data/ndvi/*.nc (descargados con lab3_appeears.py).
Salida:  scripts/salida/lab3_resumen.json, lab3_ndvi_anual.png, lab3_antes_despues.png
(se copian a mano a ../resultados para subirlos al repo)

Responde las preguntas del Laboratorio 3 de la guía 12:
  - ¿Se ve el valle verde contra el desierto? (área verde con NDVI > 0,3)
  - ¿Cuántos meses se pierden por nubes en selva y sierra? (pixel reliability = 3)
  - ¿La selva se satura? (NDVI alto y casi sin cambio)
  - Antes y después: 2001 frente a 2024.
Tendencia con lab5_tendencias.py de Josue (TFPW + Sen con IC95).
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "data" / "ndvi"
SALIDA = AQUI / "salida"  # las imágenes finales se copian a ../resultados
sys.path.insert(0, str(AQUI.parent.parent / "josue" / "scripts"))  # lab5 de Josue
from lab5_tendencias import analizar  # noqa: E402

ZONAS = [  # mismo orden que la solicitud (aid0001 … aid0006)
    ("Chavimochic (Virú-Chao)", "valle irrigado"),
    ("Olmos", "valle irrigado"),
    ("Ica (valle y Villacurí)", "valle irrigado"),
    ("Lima Metropolitana", "ciudad"),
    ("Selva cerca de Iquitos", "selva"),
    ("Valle del Mantaro (Huancayo)", "sierra"),
]
VERDE = 0.3  # NDVI desde el que consideramos vegetación (cultivo o bosque)
KM2_PIXEL = 0.9266 ** 2  # píxel MODIS de 926,6 m


def analizar_zona(i):
    ds = xr.open_dataset(DATOS / f"MOD13A3.061_1km_aid000{i + 1}.nc")
    ndvi = ds["_1_km_monthly_NDVI"].values  # (tiempo, lat, lon), ya escalado
    fiable = ds["_1_km_monthly_pixel_reliability"].values
    anios = np.array([t.year for t in ds["time"].values])
    dentro = ~np.isnan(ndvi).all(axis=0)  # píxeles del recuadro con algún dato
    n_pix = int(dentro.sum())
    bueno = np.isin(fiable, [0, 1]) & ~np.isnan(ndvi)
    limpio = np.where(bueno, ndvi, np.nan)
    # Mes perdido: más de la mitad de los píxeles sin dato confiable (nubes, sobre todo)
    frac_nube = (fiable == 3).sum(axis=(1, 2)) / max(n_pix, 1)
    frac_bueno = bueno.sum(axis=(1, 2)) / max(n_pix, 1)
    perdidos = int((frac_bueno < 0.5).sum())
    mensual = np.nanmean(limpio, axis=(1, 2))
    anual = {}
    for a in range(2001, 2025):
        sel = (anios == a) & ~np.isnan(mensual)
        if sel.sum() >= 6:  # al menos medio año con dato
            anual[a] = float(np.nanmean(mensual[sel]))
    tendencia = analizar(anual)

    def media_pixel(a):
        with np.errstate(all="ignore"):
            return np.nanmean(limpio[anios == a], axis=0)

    antes, despues = media_pixel(2001), media_pixel(2024)
    verde_antes = int(np.nansum(antes > VERDE))
    verde_despues = int(np.nansum(despues > VERDE))
    return {
        "pixeles": n_pix,
        "meses": int(len(anios)),
        "meses_perdidos": perdidos,
        "nubes_promedio_pct": round(float(np.nanmean(frac_nube)) * 100, 1),
        "ndvi_medio": round(float(np.nanmean(list(anual.values()))), 3),
        "ndvi_2001": round(anual.get(2001, float("nan")), 3),
        "ndvi_2024": round(anual.get(2024, float("nan")), 3),
        "area_verde_km2_2001": round(verde_antes * KM2_PIXEL),
        "area_verde_km2_2024": round(verde_despues * KM2_PIXEL),
        "tendencia": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in tendencia.items()},
        "_anual": anual,
        "_antes": antes,
        "_despues": despues,
        "_extent": [float(ds.lon.min()), float(ds.lon.max()), float(ds.lat.min()), float(ds.lat.max())],
    }


def main():
    SALIDA.mkdir(exist_ok=True)
    res = [analizar_zona(i) for i in range(len(ZONAS))]

    # Serie anual de las 6 zonas
    fig, ax = plt.subplots(figsize=(10, 4.4))
    for (nombre, _), r in zip(ZONAS, res):
        a = sorted(r["_anual"])
        ax.plot(a, [r["_anual"][x] for x in a], lw=2, label=nombre)
    ax.axhline(VERDE, color="grey", ls=":", lw=1)
    ax.set_ylabel("NDVI anual (0–1)")
    ax.set_title("MODIS MOD13A3, NDVI anual 2001–2024 (línea punteada: umbral de vegetación 0,3)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(SALIDA / "lab3_ndvi_anual.png", dpi=120)

    # Antes y después de los 3 valles irrigados y Lima
    fig, axs = plt.subplots(4, 2, figsize=(7.5, 13))
    for fila, i in enumerate([0, 1, 2, 3]):
        r = res[i]
        for col, (clave, anio) in enumerate([("_antes", 2001), ("_despues", 2024)]):
            ax = axs[fila, col]
            im = ax.imshow(r[clave], cmap="YlGn", vmin=0, vmax=0.8, extent=r["_extent"], origin="upper")
            ax.set_title(f"{ZONAS[i][0]} · {anio}", fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])
    fig.colorbar(im, ax=axs, shrink=0.4, label="NDVI")
    fig.savefig(SALIDA / "lab3_antes_despues.png", dpi=110, bbox_inches="tight")

    salida = {nombre: {"tipo": tipo, **{k: v for k, v in r.items() if not k.startswith("_")}}
              for (nombre, tipo), r in zip(ZONAS, res)}
    (SALIDA / "lab3_resumen.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    for nombre, r in salida.items():
        t = r["tendencia"]
        print(f"{nombre:30s} píxeles {r['pixeles']:4d} | NDVI 2001 {r['ndvi_2001']:.3f} → 2024 {r['ndvi_2024']:.3f} | "
              f"verde {r['area_verde_km2_2001']:4d} → {r['area_verde_km2_2024']:4d} km² | "
              f"Sen {t.get('slope_per_decade', float('nan')):+.4f}/déc p={t.get('p_value', float('nan')):.4f} "
              f"IC[{t.get('ci_low', float('nan')):+.4f},{t.get('ci_high', float('nan')):+.4f}] | "
              f"meses perdidos {r['meses_perdidos']}/{r['meses']} | nubes {r['nubes_promedio_pct']} %")


if __name__ == "__main__":
    main()
