"""Lab 5 — prueba de tendencia con las series anuales de POWER (salida del Lab 1).

Método de 06-datos-a-usar.md, sección 3:
  1. Mann-Kendall con pre-whitening sin tendencia (TFPW, Yue et al. 2002)
  2. Pendiente de Sen por década con IC 95 % (misma fórmula que scipy.stats.theilslopes)
  3. Benjamini-Hochberg entre zonas (q_value), por variable y periodo
  4. Estado: real / posible_casualidad / pocos_datos, con un criterio único (`estado()`):
     real solo si q < 0.05, el IC95 de Sen no incluye 0 y |lag1| <= 0.5.
     El p-valor (TFPW, serie pre-blanqueada) y el IC (Sen, serie original) son pruebas
     distintas y pueden discrepar; exigir las dos evita mostrar "real" con un IC que cruza 0.

Implementado con biblioteca estándar porque en esta máquina aún no se instalaron
pymannkendall ni scipy. Replica sus fórmulas; ver `comparar_con_librerias()`
para validarlo cuando estén instaladas.

Uso:  python3 scripts/lab5_tendencias.py            (corre la autoprueba y el análisis)
"""
import csv
import json
import math
import statistics as st
from pathlib import Path

SALIDA = Path(__file__).resolve().parent.parent / "salida"
PERIODOS = {"largo": (1981, 2024), "reciente": (2001, 2024)}  # 13-datos-unificado-14nov.md
VARIABLES = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR"]
ALFA = 0.05
MAX_LAG1 = 0.5  # con más autocorrelación ni TFPW controla bien los falsos positivos
MIN_AÑOS = 10  # 02-datasets-explicados.md: "mínimo ~10 años de datos por zona"


def norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def sen(y, x=None):
    """Pendiente de Sen y ordenada (mediana de y - b*x), como pymannkendall.sens_slope."""
    x = x or list(range(len(y)))
    pend = sorted((y[j] - y[i]) / (x[j] - x[i]) for i in range(len(y)) for j in range(i + 1, len(y)) if x[j] != x[i])
    b = st.median(pend)
    return b, st.median(yi - b * xi for xi, yi in zip(x, y)), pend


def sen_ic(y, x, confianza=0.95):
    """IC de la pendiente de Sen: misma regla que scipy.stats.theilslopes (Sen 1968, ec. 2.6)."""
    b, a, pend = sen(y, x)
    n, nt = len(y), len(pend)
    z = -_ppf((1 - confianza) / 2)  # 1.96 para 95 %
    sigma = math.sqrt(n * (n - 1) * (2 * n + 5) / 18)  # x (años) sin empates
    ru = min(int(round((nt + z * sigma) / 2)), nt - 1)
    rd = max(int(round((nt - z * sigma) / 2)) - 1, 0)
    return b, a, pend[rd], pend[ru]


def _ppf(p):
    """Inversa de la normal por bisección (suficiente para alfa/2)."""
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if norm_cdf(mid) < p else (lo, mid)
    return (lo + hi) / 2


def mk(x):
    """Mann-Kendall clásico con corrección por empates. Devuelve (s, var_s, z, p)."""
    n = len(x)
    s = sum((x[j] > x[i]) - (x[j] < x[i]) for i in range(n) for j in range(i + 1, n))
    grupos = {}
    for v in x:
        grupos[v] = grupos.get(v, 0) + 1
    var_s = (n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in grupos.values() if t > 1)) / 18
    z = 0.0 if s == 0 else (s - 1) / math.sqrt(var_s) if s > 0 else (s + 1) / math.sqrt(var_s)
    return s, var_s, z, 2 * (1 - norm_cdf(abs(z)))


def acf1(x):
    m = st.mean(x)
    den = sum((v - m) ** 2 for v in x)
    return 0.0 if den == 0 else sum((x[i] - m) * (x[i + 1] - m) for i in range(len(x) - 1)) / den


def tfpw(x):
    """Trend-free pre-whitening, como pymannkendall.trend_free_pre_whitening_modification_test."""
    n = len(x)
    t = list(range(1, n + 1))
    b, _, _ = sen(x)
    det = [x[i] - t[i] * b for i in range(n)]
    r1 = acf1(det)
    pw = [det[i] - det[i - 1] * r1 + t[i] * b for i in range(1, n)]
    s, var_s, z, p = mk(pw)
    return {"p_value": p, "z": z, "s": s, "lag1": r1}


def bh(pvals):
    """q-values de Benjamini-Hochberg (igual que statsmodels fdr_bh)."""
    m = len(pvals)
    orden = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i = orden[rank - 1]
        prev = min(prev, pvals[i] * m / rank)
        q[i] = prev
    return q


def analizar(serie):
    """serie: dict año -> valor. Devuelve los campos del contrato (06, sección 3)."""
    años = sorted(serie)
    y = [serie[a] for a in años]
    n = len(y)
    if n < MIN_AÑOS:
        return {"n_years": n, "status": "pocos_datos"}
    r = tfpw(y)
    b, a, lo, hi = sen_ic(y, años)
    media = st.mean(y)
    return {
        "year_start": años[0], "year_end": años[-1], "n_years": n,
        "slope_per_decade": b * 10, "intercept": a, "ci_low": lo * 10, "ci_high": hi * 10,
        "pct_change_per_decade": (b * 10 / media * 100) if media else None,
        "p_value": r["p_value"], "lag1": r["lag1"],
    }


def estado(r):
    """Criterio único del semáforo (docs/tendencias.md, sección 2b). Devuelve (status, motivo).

    `r` es la salida de `analizar()` con `q_value` ya añadido; si falta `q_value` (una sola
    zona, sin corrección posible) se usa `p_value`.
    """
    if "p_value" not in r:
        return "pocos_datos", f"años={r['n_years']}"
    q = r.get("q_value", r["p_value"])
    motivos = []
    if q >= ALFA:
        motivos.append(f"q={q:.3f}")
    if r["ci_low"] <= 0 <= r["ci_high"]:
        motivos.append("IC95 incluye 0")
    if abs(r["lag1"]) > MAX_LAG1:
        motivos.append(f"lag1={r['lag1']:.2f}")
    return ("real", "") if not motivos else ("posible_casualidad", "; ".join(motivos))


# Serie sintética fija (24 años) con p < 0.05 pero IC95 que cruza 0, el mismo tipo de discrepancia
# que el valle del Mantaro (NDVI) y Loreto (temperatura). Aquí p = 0.0071 (TFPW) e
# IC = [-0.0016, +0.0385] por década. Fija el comportamiento de `estado()`.
P_SI_IC_NO = [0.0716, 0.016, 0.0342, 0.0142, 0.0347, -0.0317, 0.0293, 0.0622, 0.0688, 0.0385,
              -0.0308, 0.0531, 0.0335, 0.0358, 0.0661, 0.0462, 0.0319, 0.1286, 0.0277, 0.0646,
              0.0618, 0.0552, 0.048, 0.1091]


def autoprueba():
    import random
    random.seed(1)
    años = list(range(1981, 2025))
    con = {a: 0.02 * (a - 1981) + random.gauss(0, 0.1) for a in años}  # +0.2 por década
    sin = {a: random.gauss(0, 0.1) for a in años}
    rc, rs = analizar(con), analizar(sin)
    assert rc["p_value"] < 0.01 and 0.15 < rc["slope_per_decade"] < 0.25, rc
    assert rc["ci_low"] < rc["slope_per_decade"] < rc["ci_high"], rc
    assert rs["p_value"] > 0.05, rs
    assert analizar({2000: 1, 2001: 2})["status"] == "pocos_datos"
    q = bh([0.01, 0.04, 0.03, 0.5])
    assert [round(v, 4) for v in q] == [0.04, 0.0533, 0.0533, 0.5], q
    # p < 0.05 e IC que incluye 0: nunca "real", y el motivo lo dice
    rd = analizar(dict(zip(range(2001, 2025), P_SI_IC_NO)))
    assert rd["p_value"] < 0.05 and rd["ci_low"] <= 0 <= rd["ci_high"], rd
    assert estado({**rd, "q_value": rd["p_value"]}) == ("posible_casualidad", "IC95 incluye 0"), rd
    assert estado({**rc, "q_value": 0.001}) == ("real", ""), rc
    assert estado({**rc, "q_value": 0.001, "lag1": 0.6})[0] == "posible_casualidad"
    assert estado({**rc, "q_value": 0.001, "lag1": -0.6})[0] == "posible_casualidad"  # |lag1|
    assert estado({**rc, "q_value": 0.001, "lag1": 0.5})[0] == "real"  # límite incluido
    assert estado({**rc, "q_value": ALFA})[0] == "posible_casualidad"  # q = 0.05 no es < 0.05
    assert estado({**rs, "q_value": 0.9})[0] == "posible_casualidad"
    assert estado(analizar({2000: 1, 2001: 2}))[0] == "pocos_datos"
    print("autoprueba OK")


def comparar_con_librerias(y):
    """Correr cuando estén instalados pymannkendall y scipy: deben coincidir."""
    import pymannkendall as pmk
    from scipy.stats import theilslopes
    r = pmk.trend_free_pre_whitening_modification_test(y)
    mio = tfpw(y)
    print("p pymannkendall", r.p, "| p propio", mio["p_value"])
    print("theilslopes", theilslopes(y, range(len(y)), 0.95), "| propio", sen_ic(y, list(range(len(y)))))


def main():
    autoprueba()
    filas = list(csv.DictReader(open(SALIDA / "lab1_power_anual.csv")))
    resultados = []
    for nombre_p, (ini, fin) in PERIODOS.items():
        for var in VARIABLES:
            bloque = []
            for punto in sorted({f["punto"] for f in filas}):
                serie = {int(f["anio"]): float(f["media_anual"]) for f in filas
                         if f["punto"] == punto and f["variable"] == var and ini <= int(f["anio"]) <= fin}
                bloque.append({"periodo": nombre_p, "variable": var, "punto": punto, **analizar(serie)})
            con_p = [r for r in bloque if "p_value" in r]
            for r, q in zip(con_p, bh([r["p_value"] for r in con_p])):
                r["q_value"] = q
                r["status"], r["motivo"] = estado(r)
            resultados += bloque
    (SALIDA / "lab5_tendencias.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    cols = ["periodo", "variable", "punto", "year_start", "year_end", "n_years", "slope_per_decade",
            "ci_low", "ci_high", "pct_change_per_decade", "p_value", "q_value", "lag1", "status", "motivo"]
    with open(SALIDA / "lab5_tendencias.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(resultados)
    for r in resultados:
        print(f"{r['periodo']:8} {r['variable']:11} {r['punto']:8} n={r['n_years']} "
              f"pend/dec={r['slope_per_decade']:+.3f} IC=[{r['ci_low']:+.3f},{r['ci_high']:+.3f}] "
              f"p={r['p_value']:.4f} q={r['q_value']:.4f} lag1={r['lag1']:+.2f} {r['status']}")


if __name__ == "__main__":
    main()
