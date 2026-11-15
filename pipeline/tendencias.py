"""Tendencias por departamento: lee data/power.json (lluvia y temperatura, NASA POWER)
y data/gpm.json (lluvia IMERG, segunda fuente para comparar) y data/ndvi_departamentos.json
(vegetación, NDVI de MODIS; lo escribe pipeline/vegetacion_malla.py) y escribe los archivos del
contrato del Drive (07-stack-decidido) en data/:

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
- status: pocos_datos si n_years < 20 o celdas < 4; real solo con el criterio
  único de tendencia_comun.py (q < 0.05, IC95 sin 0, |lag1| <= 0.5); si no,
  posible_casualidad. La lluvia de IMERG (lluvia_imerg) nunca sale real: el salto
  de 2014 puede fingir la tendencia.
- aviso (texto): siempre en lluvia_imerg (salto de 2014), si |lag1| > 0.5 y si
  la prueba es significativa pero el IC incluye 0 (explica por qué no es real), y el de
  Ucayali en temperatura (AVISOS_ZONA: su subida depende de 2023–2024).
"""
import json
from pathlib import Path

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes
from statsmodels.stats.multitest import multipletests

from departamentos import MIN_CELDAS, UBIGEO
from tendencia_comun import AVISO_LAG1, evaluar  # noqa: F401  AVISO_LAG1 lo usan las pruebas

DATA = Path(__file__).parent.parent / "data"
PERIODO = (2001, 2024)  # decidido el 2026-11-14, el mismo para las dos variables
P_MIN = 1e-6  # menor p/q que se publica; el front muestra «< 0,000001» cuando vale esto
MIN_ANIOS = 20  # ALFA y MAX_LAG1 viven en tendencia_comun.py (criterio único)

def _coma(x, decimales=1):
    return f"{x:.{decimales}f}".replace(".", ",")


def aviso_ucayali(anios, y, st):
    """Ucayali sube más que ningún otro departamento y pesa el final de la serie (docs/datos.md,
    «Ucayali: la tendencia más alta»). Los números salen de la serie: no quedan viejos al regenerar."""
    antes = y[:-2]
    sin_final = theilslopes(antes, anios[:-2])[0] * 10
    return (f"La subida depende del final de la serie: {anios[-2]} y {anios[-1]} salieron mucho más "
            f"calientes ({_coma(y[-2])} y {_coma(y[-1])} °C, frente a {_coma(antes.min())}–{_coma(antes.max())} °C "
            f"en los años anteriores). Sin esos dos años la subida baja de {_coma(st['slope_per_decade'], 2)} a "
            f"{_coma(sin_final, 2)} °C por década. Con estos datos no se puede separar calentamiento real, "
            "calor extremo de esos años y un cambio en el reanálisis.")


def aviso_saturado(anios, y, st):
    """En la selva el NDVI ronda 0,8 casi siempre: no ve la pérdida de bosque (docs/vegetacion.md)."""
    if y.mean() >= SATURADO:
        return (f"El NDVI de este departamento ronda {_coma(y.mean(), 2)}, casi saturado: en la selva "
                "apenas cambia aunque se pierda bosque. Para el bosque, mira la cobertura de árboles.")
    return None


SATURADO = 0.75  # NDVI medio desde el que se avisa saturación

# unidad, fuente y descripcion: mismos textos que src/models/variable.rs
# El orden es el de Variable::TODAS en src/models/variable.rs.
VARIABLES = {
    # Lluvia principal: NASA POWER, la misma fuente y el mismo criterio que la temperatura
    # (opción C, 2026-11-15). IMERG baja en 25 de 25 departamentos por el salto de 2014;
    # POWER no tiene ese salto. IMERG queda como segunda fuente para comparar.
    "lluvia": {
        "archivo": "power.json", "campo": "PRECTOTCORR",
        "unidad": "mm/día", "fuente": "MERRA-2 vía NASA POWER (PRECTOTCORR)",
        "descripcion": "Lluvia: promedio diario de cada año",
        "porcentaje": True,
    },
    "temperatura": {
        "archivo": "power.json", "campo": "T2M",
        "unidad": "°C", "fuente": "MERRA-2 vía NASA POWER (T2M)",
        "descripcion": "Temperatura del aire a 2 m: promedio de cada año",
        "porcentaje": False,
        # Aviso propio de una zona (ubigeo → función(anios, y, stats) → texto); va delante del de lag1
        "avisos_zona": {"25": aviso_ucayali},
    },
    # Segunda fuente de lluvia, solo para «¿Coinciden dos fuentes de NASA?»: no va en el selector.
    "lluvia_imerg": {
        "archivo": "gpm.json", "campo": "lluvia_mm_dia",
        "unidad": "mm/día", "fuente": "GPM IMERG v07 (NASA)",
        "descripcion": "Lluvia por satélite (segunda fuente, para comparar con POWER)",
        "porcentaje": True,
        # Regla 3b: la NASA advierte saltos de homogeneidad al pasar de TRMM a GPM.
        "aviso": "IMERG cambia de constelación de satélites en 2014 (TRMM → GPM): "
                 "la tendencia de lluvia puede estar sesgada a la baja, por eso no se marca como real.",
        "sin_real": True,
    },
    # Vegetación: NDVI anual de MODIS por departamento, de la malla de 0,25° (pipeline/vegetacion_malla.py)
    "vegetacion": {
        "archivo": "ndvi_departamentos.json", "campo": "ndvi",
        "unidad": "NDVI", "fuente": "MODIS MOD13A3 v061 (NDVI) vía AppEEARS",
        "descripcion": "Vegetación (NDVI de MODIS): promedio de cada año",
        "porcentaje": False,
        "aviso_si": aviso_saturado,
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


def clasificar(st, q, celdas, aviso=None, sin_real=False):
    """Añade p_value/q_value redondeados, status y aviso. El status se decide
    con los valores publicados, para que el JSON nunca se contradiga."""
    # Piso de 1e-6: un p o q que redondea a 0 se publica como 0.000001 («p ≤ 0,000001»), nunca como 0
    st["p_value"] = max(round(st["p_value"], 6), P_MIN)
    st["q_value"] = max(round(float(q), 6), P_MIN)
    es_real, avisos = evaluar(st["q_value"], st["ci_low"], st["ci_high"], st["lag1"])
    if st["n_years"] < MIN_ANIOS or celdas < MIN_CELDAS:
        st["status"] = "pocos_datos"
    elif es_real and not sin_real:
        st["status"] = "real"
    else:
        st["status"] = "posible_casualidad"
    avisos = [aviso, *avisos]
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


def escribir(ruta, contenido, salto_final=False):
    """Único escritor de data/*.json (también lo usan ndvi.py y cobertura.py, que terminan en salto de
    línea). allow_nan=False: un NaN rompe aquí, no en la API."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(contenido, ensure_ascii=False, indent=1, allow_nan=False)
    ruta.write_text(texto + ("\n" if salto_final else ""), encoding="utf-8")


def main():
    variables = []
    for var, cfg in VARIABLES.items():
        zonas = zonas_de(cfg)
        stats = [estadisticas(a, y, cfg["porcentaje"]) for _, a, y in zonas]
        qs = multipletests([s["p_value"] for s in stats], method="fdr_bh")[1]

        resumen = []
        for (fila, anios, y), st, q in zip(zonas, stats, qs):
            propio = cfg.get("avisos_zona", {}).get(UBIGEO[fila["region"]])
            segun = cfg.get("aviso_si")
            aviso = " ".join(filter(None, [cfg.get("aviso"), propio and propio(anios, y, st),
                                           segun and segun(anios, y, st)]))
            clasificar(st, q, fila["celdas"], aviso or None, cfg.get("sin_real", False))
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
