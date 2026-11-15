"""Vegetación (NDVI) de los valles irrigados de la costa -> data/ndvi.json.

Fuente: MODIS MOD13A3 v061 (NASA LP DAAC), NDVI mensual a 1 km, pedido a AppEEARS.
Origen: Lab 3 de Favio (pipeline/exploracion/favio/scripts/lab3_analisis.py), con las
reglas de docs/reglas-datos.md y el método de docs/tendencias.md (el mismo de
pipeline/tendencias.py: scipy, pymannkendall, Benjamini-Hochberg y el criterio único).

Uso (desde la raíz del repo):
  python pipeline/ndvi.py enviar      crea la solicitud en AppEEARS y guarda el task_id
  python pipeline/ndvi.py estado      consulta la solicitud (tarda ~3 h)
  python pipeline/ndvi.py bajar       descarga los NetCDF a pipeline/cache/ndvi/ (no se suben)
  python pipeline/ndvi.py calcular    NetCDF -> data/ndvi.json
  python pipeline/ndvi.py autoprueba  prueba la lógica sin red ni NetCDF (la corre tests/e2e.sh)

Refresco: a mano, una vez al año (enero), no en el cron: AppEEARS tarda ~3 h por solicitud.
AppEEARS (credenciales, solicitud, descarga): pipeline/appeears.py, compartido con cobertura.py.

Zonas: solo los valles irrigados confirmados (docs/vegetacion.md). Olmos entra con un recuadro
nuevo (2026-11-15) y con aviso: el del Lab 3 cayó sobre bosque seco y se descartó tras ver su
resultado; esa prueba descartada se cuenta en Benjamini-Hochberg (PRUEBAS_DESCARTADAS). Fuera: selva
(NDVI saturado; ver pipeline/cobertura.py), Lima (garúa: años incompletos) y Mantaro (IC que incluye 0).

Reproducir data/ndvi.json: el archivo publicado salió de dos solicitudes (44445de3: Chavimochic e
Ica, la del Lab 3; ee736bc9: Olmos). Hoy `enviar` pide las 3 zonas en una sola solicitud, así que
enviar → estado → bajar → calcular lo reproduce entero.

Área verde: píxeles cuyo NDVI medio del año (meses con dato confiable de ese píxel,
como en el Lab 3) supera 0,3, por el área del píxel.
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np
from statsmodels.stats.multitest import multipletests

import appeears
import tendencias
from tendencias import clasificar, estadisticas

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "pipeline" / "cache" / "ndvi"  # en .gitignore
TASK = CACHE / "task.json"
SALIDA = RAIZ / "data" / "ndvi.json"
PRODUCTO = "MOD13A3.061"

FUENTE = "MODIS MOD13A3 v061 (NASA LP DAAC) vía AppEEARS"
ANIOS = range(2001, 2025)  # MODIS empieza en feb 2000: 2000 nunca es año completo
VERDE = 0.3  # NDVI desde el que un píxel cuenta como vegetación (Lab 3)
KM2_PIXEL = 0.9266 ** 2  # píxel MODIS de 926,6 m
MIN_FRAC_PIXELES = 0.5  # un mes vale si al menos la mitad de los píxeles tiene dato confiable
CAPAS = ["_1_km_monthly_NDVI", "_1_km_monthly_pixel_reliability"]

ZONAS = [  # (id, nombre, departamento, ubigeo, tipo, (oeste, sur, este, norte))
    # Chavimochic e Ica: las mismas cajas del Lab 3
    ("chavimochic", "Chavimochic (Virú-Chao)", "La Libertad", "13", "valle irrigado", (-78.85, -8.60, -78.60, -8.35)),
    ("ica-villacuri", "Ica (valle y Villacurí)", "Ica", "11", "valle irrigado", (-75.90, -14.15, -75.65, -13.90)),
    # Olmos: caja nueva. La del Lab 3 (-80.00, -6.10, -79.75, -5.85) se descartó DESPUÉS de ver su
    # resultado (bosque seco, p = 0,43). La nueva es la caja de 0,25° con más campos de cultivo en
    # OpenStreetMap (landuse=farmland/orchard, ~4.400 polígonos; Overpass, 2026-11-15), elegida antes
    # de ver su propio NDVI. Mide ~765 km² y mezcla riego con bosque seco: ver AVISOS.
    ("olmos", "Olmos (tierras nuevas)", "Lambayeque", "14", "valle irrigado", (-80.15, -6.25, -79.90, -6.00)),
]
# Pruebas hechas y descartadas que también cuentan en Benjamini-Hochberg (honestidad estadística):
# la caja de Olmos del Lab 3 (pipeline/exploracion/favio/resultados/lab3_resumen.json).
PRUEBAS_DESCARTADAS = [0.4282]
# Aviso por zona (va en stats.aviso y la ficha lo muestra).
AVISOS = {
    "olmos": ("Recuadro movido después de descartar el del Lab 3 (caía sobre bosque seco y no tenía "
              "tendencia). Mezcla tierras de riego con bosque seco, y la subida pesa mucho en los años "
              "de El Niño (2015–2017 y 2023): sin ellos, el rango probable incluye 0."),
}
UNIDAD_GEO = ("recuadro de 0,25° × 0,25° (~27 × 27 km) sobre el valle irrigado; "
              "no es el promedio del departamento")


# ---------- lógica (sin red ni NetCDF: se prueba en autoprueba) ----------

def anual(meses, areas):
    """Serie anual con solo años completos (reglas-datos.md §1).

    meses: [(anio, mes, valido, ndvi_mes)] · areas: {anio: km2 verdes con el NDVI medio del año}.
    Devuelve {anio: {"ndvi_anual", "area_verde_km2"}} solo para años de ANIOS con los 12 meses
    distintos válidos (un mes repetido no tapa uno que falta).
    """
    por_anio = {}
    for anio, mes, valido, ndvi in meses:
        if valido:
            por_anio.setdefault(anio, {})[mes] = ndvi
    return {
        a: {"ndvi_anual": round(sum(m.values()) / 12, 4), "area_verde_km2": round(areas[a], 1)}
        for a, m in sorted(por_anio.items())
        if a in ANIOS and set(m) == set(range(1, 13))
    }


def zona_json(zona, pixeles, serie):
    """Fila de data/ndvi.json. `stats` (sobre ndvi_anual) aún sin q_value ni status."""
    zid, nombre, depto, ubigeo, tipo, (o, s, e, n) = zona
    anios = np.array(sorted(serie))
    y = np.array([serie[a]["ndvi_anual"] for a in anios], dtype=float)
    st = estadisticas(anios, y, porcentaje=False) if len(y) >= 3 else {"n_years": len(y)}
    return {
        "id": zid, "nombre": nombre, "departamento": depto, "ubigeo": ubigeo, "tipo": tipo,
        "unidad_geografica": UNIDAD_GEO, "bbox": [o, s, e, n],
        "lat": round((s + n) / 2, 3), "lon": round((o + e) / 2, 3),
        "pixeles": pixeles, "fuente": FUENTE, "umbral_verde_ndvi": VERDE,
        "tendencia_de": "ndvi_anual",
        "serie": [{"anio": int(a), **v} for a, v in sorted(serie.items())],
        "stats": st,
    }


def con_estado(filas, descartadas=PRUEBAS_DESCARTADAS):
    """q_value (BH entre las zonas con prueba y las pruebas descartadas), status y aviso con
    clasificar() de tendencias.py. Las descartadas solo suman a la corrección: no se publican."""
    con_p = [f for f in filas if "p_value" in f["stats"]]
    ps = [f["stats"]["p_value"] for f in con_p] + list(descartadas)
    qs = multipletests(ps, method="fdr_bh")[1][: len(con_p)] if con_p else []
    for f, q in zip(con_p, qs):
        clasificar(f["stats"], q, f["pixeles"], AVISOS.get(f["id"]))
    for f in filas:
        if "p_value" not in f["stats"]:
            f["stats"]["status"] = "pocos_datos"
    return filas


def escribir(filas, ruta=SALIDA):
    tendencias.escribir(ruta, filas, salto_final=True)


# ---------- AppEEARS (red): pipeline/appeears.py ----------

def enviar(zonas=None, task=None, nombre="detective-peru-ndvi"):
    """Crea la solicitud en AppEEARS (por defecto, todas las ZONAS) y guarda el task_id en `task`."""
    appeears.enviar(zonas or ZONAS, PRODUCTO, CAPAS, ANIOS, task or TASK, nombre)


def consultar(task=None):
    appeears.consultar(task or TASK)


def bajar(task=None, destino_dir=None):
    """Descarga los NetCDF de la solicitud a `destino_dir` (por defecto, la caché de ndvi)."""
    appeears.bajar(task or TASK, destino_dir or CACHE)


# ---------- NetCDF -> data/ndvi.json ----------

def _leer_zona(zona):
    """NetCDF cuyo centro cae en la caja de la zona -> (pixeles, meses, areas)."""
    import xarray as xr
    with xr.open_dataset(appeears.nc_de_zona(CACHE, zona)) as ds:
        ndvi, fiable = ds[CAPAS[0]].values, ds[CAPAS[1]].values  # (tiempo, lat, lon), NDVI ya escalado
        # .dt sirve con datetime64 y con cftime (calendario juliano de AppEEARS); t.year solo con cftime
        anios, mes = ds["time"].dt.year.values, ds["time"].dt.month.values
    pixeles = int((~np.isnan(ndvi).all(axis=0)).sum())
    bueno = np.isin(fiable, [0, 1]) & ~np.isnan(ndvi)
    limpio = np.where(bueno, ndvi, np.nan)
    frac = bueno.sum(axis=(1, 2)) / max(pixeles, 1)
    with np.errstate(all="ignore"):
        media_mes = np.nanmean(limpio, axis=(1, 2))
        areas = {int(a): float((np.nanmean(limpio[anios == a], axis=0) > VERDE).sum() * KM2_PIXEL)
                 for a in np.unique(anios)}
    meses = [(int(a), int(m), bool(f >= MIN_FRAC_PIXELES), float(v))
             for a, m, f, v in zip(anios, mes, frac, media_mes)]
    return pixeles, meses, areas


def calcular():
    filas = []
    for zona in ZONAS:
        pixeles, meses, areas = _leer_zona(zona)
        serie = anual(meses, areas)
        if len(serie) < len(ANIOS):
            print(f"aviso: {zona[1]} tiene {len(serie)} de {len(ANIOS)} años completos")
        filas.append(zona_json(zona, pixeles, serie))
    escribir(con_estado(filas))
    for f in filas:
        st, a = f["stats"], {p["anio"]: p for p in f["serie"]}
        extremos = " · ".join(f"{k}: NDVI {a[k]['ndvi_anual']}, {a[k]['area_verde_km2']} km²" for k in (2001, 2024) if k in a)
        print(f"{f['nombre']}: {st['n_years']} años, Sen {st.get('slope_per_decade', 0):+.4f}/déc "
              f"IC [{st.get('ci_low')}, {st.get('ci_high')}], {st['status']} · {extremos}")


def autoprueba():
    # Años completos: entra 2001; no entran 2002 (falta julio), 2003 (julio repetido tapa agosto),
    # 2000 y 2025 (fuera de 2001-2024 aunque tengan 12 meses).
    meses = [(2001, m, True, 0.2) for m in range(1, 13)]
    meses += [(2002, m, m != 7, 0.3) for m in range(1, 13)]
    meses += [(2003, 7 if m == 8 else m, True, 0.3) for m in range(1, 13)]
    meses += [(a, m, True, 0.1) for a in (2000, 2025) for m in range(1, 13)]
    serie = anual(meses, {a: 100.0 for a in range(2000, 2026)})
    assert list(serie) == [2001] and serie[2001] == {"ndvi_anual": 0.2, "area_verde_km2": 100.0}, serie

    azar = np.random.default_rng(1)

    def zona(pendiente, ruido, anios=ANIOS):
        return {a: {"ndvi_anual": float(0.2 + pendiente * (a - 2001) + azar.normal(0, ruido)),
                    "area_verde_km2": 1.0} for a in anios}

    filas = con_estado([
        zona_json(ZONAS[0], 847, zona(0.005, 0.005)),            # reverdece: real
        zona_json(ZONAS[1], 900, zona(0.0, 0.01)),               # sin tendencia: posible_casualidad
        zona_json(ZONAS[1], 900, zona(0.005, 0.005, range(2001, 2013))),  # 12 años: pocos_datos
        zona_json(ZONAS[1], 900, {}),                             # sin años: pocos_datos sin prueba
    ])
    estados = [f["stats"]["status"] for f in filas]
    assert estados == ["real", "posible_casualidad", "pocos_datos", "pocos_datos"], estados
    assert all("q_value" in f["stats"] for f in filas[:3]) and "q_value" not in filas[3]["stats"]
    texto = json.dumps(filas, allow_nan=False)
    assert "NaN" not in texto and "null" not in texto
    assert filas[0]["ubigeo"] == "13" and "no es el promedio del departamento" in filas[0]["unidad_geografica"]
    ids = [z[0] for z in ZONAS]
    assert ids == ["chavimochic", "ica-villacuri", "olmos"], ids
    for zid, _, _, _, _, (o, s_, e, n) in ZONAS:
        assert o < e and s_ < n, zid
    fila = zona_json(ZONAS[2], 900, zona(0.005, 0.005))
    assert fila["bbox"][0] <= fila["lon"] <= fila["bbox"][2] and fila["bbox"][1] <= fila["lat"] <= fila["bbox"][3]
    olmos = con_estado([zona_json(ZONAS[0], 847, zona(0.005, 0.005)), fila])[1]
    assert "Lab 3" in olmos["stats"]["aviso"], "Olmos lleva su aviso"
    # La prueba descartada sube los q: con [p, descartada] el q de p no puede bajar
    base = zona_json(ZONAS[0], 847, zona(0.0, 0.01))
    sin = con_estado([copy.deepcopy(base)], descartadas=[])[0]["stats"]["q_value"]
    con = con_estado([copy.deepcopy(base)])[0]["stats"]["q_value"]
    assert con >= sin, (sin, con)
    print("autoprueba ndvi OK")


if __name__ == "__main__":
    acciones = {"enviar": enviar, "estado": consultar, "bajar": bajar, "calcular": calcular, "autoprueba": autoprueba}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        sys.exit(f"uso: python pipeline/ndvi.py {{{'|'.join(acciones)}}}")
    acciones[sys.argv[1]]()
