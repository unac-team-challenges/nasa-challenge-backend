"""Tendencias por departamento: lee data/power.json (temperatura) y
data/gpm.json (lluvia, IMERG) y escribe los archivos del contrato del
Drive (07-stack-decidido) en data/:

  data/variables.json                 -> GET /api/variables
  data/zonas/{variable}.json          -> GET /api/zonas?variable=        (sin serie)
  data/zonas/{variable}/{id}.json     -> GET /api/zonas/{id}?variable=   (serie + stats)

Uso: python pipeline/tendencias.py

Periodo: PERIODO (2001–2024) para las dos variables, aunque el cron añada
años a los JSON de entrada. Método (docs/tendencias.md), sobre la serie anual:
- Mann-Kendall con pre-blanqueo sin tendencia (TFPW, pymannkendall) -> p_value
- Pendiente de Sen e intervalo 95 % (scipy.stats.theilslopes) x 10 -> por década
- Benjamini-Hochberg entre las 25 zonas de la misma variable -> q_value
- lag1: autocorrelación de la serie sin tendencia (como lab5 de Josue)
- status: pocos_datos si n_years < 20 o celdas < 4; real si q < 0.05;
  si no, posible_casualidad.
- aviso (texto): siempre en lluvia (salto de IMERG en 2014) y si lag1 > 0.5.
"""
import json
from pathlib import Path

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes
from statsmodels.stats.multitest import multipletests

from departamentos import MIN_CELDAS, UBIGEO

DATA = Path(__file__).parent.parent / "data"
PERIODO = (2001, 2024)  # decidido el 2026-11-14, el mismo para las dos variables
MIN_ANIOS, MAX_LAG1, ALFA = 20, 0.5, 0.05

AVISO_LAG1 = "Años muy parecidos entre sí (lag1 alto): la tendencia puede parecer más segura de lo que es"

# unidad, fuente y descripcion: mismos textos que src/models/variable.rs
VARIABLES = {
    "lluvia": {
        "archivo": "gpm.json", "campo": "lluvia_mm_dia",
        "unidad": "mm/día", "fuente": "GPM IMERG v07 (NASA)",
        "descripcion": "Lluvia: promedio diario de cada año",
        "porcentaje": True,
        # Regla 3b: la NASA advierte saltos de homogeneidad al pasar de TRMM a GPM.
        "aviso": "IMERG cambia de constelación de satélites en 2014 (TRMM → GPM): "
                 "la tendencia de lluvia puede estar sesgada a la baja.",
    },
    "temperatura": {
        "archivo": "power.json", "campo": "T2M",
        "unidad": "°C", "fuente": "MERRA-2 vía NASA POWER (T2M)",
        "descripcion": "Temperatura del aire a 2 m: promedio de cada año",
        "porcentaje": False,
    },
}


def lag1(anios, y, pendiente):
    """Autocorrelación de un año al siguiente, sin la tendencia de Sen."""
    det = y - pendiente * (anios - anios[0])
    det = det - det.mean()
    den = float((det ** 2).sum())
    return 0.0 if den == 0 else float((det[:-1] * det[1:]).sum() / den)


def estadisticas(anios, y, porcentaje):
    """Campos del contrato salvo q_value y status (dependen de las 25 zonas).
    p_value va sin redondear: Benjamini-Hochberg lo usa tal cual."""
    pend, intercepto, lo, hi = theilslopes(y, anios, alpha=0.95)
    st = {
        "year_start": int(anios[0]), "year_end": int(anios[-1]), "n_years": len(y),
        # 6 decimales: la recta se reconstruye con el año real (~2000 × pendiente)
        "slope_per_decade": round(pend * 10, 6),
        "intercept": round(intercepto, 6),  # valor = intercept + slope_per_decade / 10 * anio
        "ci_low": round(lo * 10, 4), "ci_high": round(hi * 10, 4),
        "p_value": float(mk.trend_free_pre_whitening_modification_test(y).p),
        "lag1": round(lag1(anios, y, pend), 4),
    }
    if porcentaje:  # solo lluvia: "x % por década" respecto a la media del periodo
        st["pct_change_per_decade"] = round(pend * 10 / y.mean() * 100, 2)
    return st


def clasificar(st, q, celdas, aviso=None):
    """Añade p_value/q_value redondeados, status y aviso. El status se decide
    con el q_value publicado, para que el JSON nunca se contradiga."""
    st["p_value"] = round(st["p_value"], 6)
    st["q_value"] = round(float(q), 6)
    if st["n_years"] < MIN_ANIOS or celdas < MIN_CELDAS:
        st["status"] = "pocos_datos"
    elif st["q_value"] < ALFA:
        st["status"] = "real"
    else:
        st["status"] = "posible_casualidad"
    avisos = [aviso, AVISO_LAG1 if st["lag1"] > MAX_LAG1 else None]
    if any(avisos):
        st["aviso"] = " ".join(filter(None, avisos))
    return st


def zonas_de(cfg):
    """[(fila de data/*.json, años, valores)] dentro de PERIODO."""
    ini, fin = PERIODO
    salida = []
    for r in json.loads((DATA / cfg["archivo"]).read_text(encoding="utf-8")):
        anios = sorted(int(a) for a in r["anios"] if ini <= int(a) <= fin)
        y = np.array([r["anios"][str(a)][cfg["campo"]] for a in anios], dtype=float)
        salida.append((r, np.array(anios), y))
    return salida


def escribir(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")


def main():
    variables = []
    for var, cfg in VARIABLES.items():
        zonas = zonas_de(cfg)
        stats = [estadisticas(a, y, cfg["porcentaje"]) for _, a, y in zonas]
        qs = multipletests([s["p_value"] for s in stats], method="fdr_bh")[1]

        resumen = []
        for (fila, anios, y), st, q in zip(zonas, stats, qs):
            clasificar(st, q, fila["celdas"], cfg.get("aviso"))
            zona = {"id": UBIGEO[fila["region"]], "nombre": fila["region"],
                    "lat": fila["lat"], "lon": fila["lon"], "celdas": fila["celdas"]}
            if "nota" in fila:
                zona["nota"] = fila["nota"]
            resumen.append({**zona, "stats": st})
            escribir(DATA / "zonas" / var / f"{zona['id']}.json", {
                **zona, "variable": var, "unidad": cfg["unidad"], "fuente": cfg["fuente"],
                "serie": [{"anio": int(a), "valor": round(float(v), 4)} for a, v in zip(anios, y)],
                "stats": st,
            })
        escribir(DATA / "zonas" / f"{var}.json", sorted(resumen, key=lambda z: z["id"]))

        variables.append({"id": var, "unidad": cfg["unidad"], "fuente": cfg["fuente"],
                          "descripcion": cfg["descripcion"],
                          "anio_inicio": min(s["year_start"] for s in stats),
                          "anio_fin": max(s["year_end"] for s in stats)})
        conteo = {e: sum(z["stats"]["status"] == e for z in resumen)
                  for e in ("real", "posible_casualidad", "pocos_datos")}
        print(f"{var}: {conteo}", flush=True)
    escribir(DATA / "variables.json", variables)


if __name__ == "__main__":
    main()
