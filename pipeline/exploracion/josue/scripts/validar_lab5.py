"""Valida la implementación propia de lab5_tendencias.py contra las librerías del stack.

Compara, para TODAS las series anuales departamentales de POWER (4 variables × 24 deptos × 2 periodos):
  p-valor TFPW     vs pymannkendall.trend_free_pre_whitening_modification_test
  Sen + IC95       vs scipy.stats.theilslopes
  q-values BH      vs statsmodels.stats.multitest.multipletests(method="fdr_bh")
Salida: salida/validacion_lab5.json  (diferencia máxima por campo)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pymannkendall as pmk
from scipy.stats import theilslopes
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab5_tendencias import bh, sen_ic, tfpw  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
df = pd.read_csv(RAIZ / "salida" / "power_departamentos_anual.csv", dtype={"ubigeo": str})
dif = {"p_tfpw": 0.0, "sen": 0.0, "ci_low": 0.0, "ci_high": 0.0, "q_bh": 0.0}
n = 0
for (var, dep), g in df.groupby(["variable", "ubigeo"]):
    for ini in (1981, 2001):
        s = g[g["anio"].between(ini, 2024)].sort_values("anio")
        if len(s) < 10:
            continue
        y, x = s["media_anual"].tolist(), s["anio"].tolist()
        ref = pmk.trend_free_pre_whitening_modification_test(np.array(y))
        dif["p_tfpw"] = max(dif["p_tfpw"], abs(ref.p - tfpw(y)["p_value"]))
        b, _, lo, hi = sen_ic(y, x)
        rb, _, rlo, rhi = theilslopes(y, x, 0.95)
        dif["sen"] = max(dif["sen"], abs(b - rb))
        dif["ci_low"] = max(dif["ci_low"], abs(lo - rlo))
        dif["ci_high"] = max(dif["ci_high"], abs(hi - rhi))
        n += 1
rng = np.random.default_rng(0)
for _ in range(200):
    p = rng.uniform(0, 1, 25).tolist()
    dif["q_bh"] = max(dif["q_bh"], float(np.max(np.abs(np.array(bh(p)) - multipletests(p, method="fdr_bh")[1]))))
res = {"series_comparadas": n, "diferencia_maxima": dif}
(RAIZ / "salida" / "validacion_lab5.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
