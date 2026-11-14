"""Gráficos PNG para los documentos (matplotlib).

  salida/lab1_caso1_lluvia.png        lluvia anual POWER: Piura, Tumbes, Puno (guía 12, Lab 1)
  salida/tendencia_t2m_departamentos.png  pendiente de T2M por departamento con IC95 y estado
  salida/tendencia_lluvia_departamentos.png  idem para PRECTOTCORR (3.ª opinión)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
S = RAIZ / "salida"
COLOR = {"real": "#1f77b4", "posible_casualidad": "#bbbbbb", "pocos_datos": "#e6a23c"}

a = pd.read_csv(S / "lab1_power_anual.csv")
fig, ax = plt.subplots(figsize=(9, 4))
for p in ["Piura", "Tumbes", "Puno"]:
    s = a[(a.punto == p) & (a.variable == "PRECTOTCORR")]
    ax.plot(s.anio, s.media_anual, marker=".", label=p)
for año in (1983, 1998, 2017):
    ax.axvline(año, color="#999", lw=0.8, ls="--")
ax.set_ylabel("Lluvia media anual (mm/día)")
ax.set_title("POWER PRECTOTCORR 1981–2024 · líneas: años El Niño 1983, 1998, 2017")
ax.legend()
fig.tight_layout()
fig.savefig(S / "lab1_caso1_lluvia.png", dpi=120)

t = pd.read_csv(S / "power_departamentos_tendencias.csv", dtype={"ubigeo": str})
for var, unidad, nombre in [("T2M", "°C por década", "t2m"), ("PRECTOTCORR", "mm/día por década", "lluvia")]:
    fig, axs = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    orden = t[(t.variable == var) & (t.periodo == "largo")].sort_values("slope_per_decade")["departamento"]
    for ax, per in zip(axs, ["largo", "reciente"]):
        d = t[(t.variable == var) & (t.periodo == per)].set_index("departamento").reindex(orden).dropna(subset=["slope_per_decade"])
        y = range(len(d))
        ax.errorbar(d.slope_per_decade, list(y), xerr=[d.slope_per_decade - d.ci_low, d.ci_high - d.slope_per_decade],
                    fmt="none", ecolor="#666", lw=1)
        ax.scatter(d.slope_per_decade, list(y), c=[COLOR[s] for s in d.status], zorder=3)
        ax.axvline(0, color="k", lw=0.8)
        ax.set_yticks(list(y), d.index)
        ax.set_title(f"{var} · {per} ({int(d.year_start.min())}–{int(d.year_end.max())})")
        ax.set_xlabel(unidad)
    axs[1].scatter([], [], c=COLOR["real"], label="real")
    axs[1].scatter([], [], c=COLOR["posible_casualidad"], label="posible_casualidad")
    axs[1].scatter([], [], c=COLOR["pocos_datos"], label="pocos_datos")
    axs[1].legend(loc="lower right")
    fig.suptitle(f"POWER por departamento: pendiente de Sen e IC95 (umbral exigente)")
    fig.tight_layout()
    fig.savefig(S / f"tendencia_{nombre}_departamentos.png", dpi=110)
print("PNG listos")
