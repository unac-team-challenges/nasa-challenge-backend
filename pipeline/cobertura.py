"""Cobertura de árboles de la selva -> data/cobertura_arboles.json.

Fuente: MODIS MOD44B v061 (Vegetation Continuous Fields, NASA LP DAAC): porcentaje de cada píxel
de 250 m cubierto por árboles, un valor por año, pedido a AppEEARS. En la selva reemplaza al NDVI,
que se satura en ~0,85 y no ve la pérdida de bosque (docs/vegetacion.md). Es otra variable y otro
JSON (docs/reglas-datos.md, regla 3): no se mezcla con data/ndvi.json.

Uso (desde la raíz del repo):
  python pipeline/cobertura.py enviar      crea la solicitud en AppEEARS y guarda el task_id
  python pipeline/cobertura.py estado      consulta la solicitud (tarda ~1–3 h)
  python pipeline/cobertura.py bajar       descarga los NetCDF a pipeline/cache/cobertura/ (no se suben)
  python pipeline/cobertura.py calcular    NetCDF -> data/cobertura_arboles.json
  python pipeline/cobertura.py autoprueba  prueba la lógica sin red ni NetCDF (la corre tests/e2e.sh)

Refresco: a mano, una vez al año, como ndvi.py (no va en el cron).
Credenciales: las mismas de ndvi.py (EARTHDATA_* del entorno o ~/.netrc / ~/_netrc). Nunca se imprimen.

Zonas (recuadros de 0,25°, no el departamento):
- La Pampa (Madre de Dios): epicentro de la deforestación por minería de oro aluvial en 2014–2018,
  en la zona de amortiguamiento de la Reserva Nacional Tambopata (MAAP / Amazon Conservation).
  Centrado en el poblado de La Pampa (OpenStreetMap: -12.962, -70.001).
- Selva cerca de Iquitos (Loreto): el mismo recuadro del Lab 3, bosque sin un frente de pérdida
  conocido; sirve de contraste (su tendencia no es distinguible de 0).

Bosque: píxeles con 30 % o más de cobertura de árboles (el umbral de Global Forest Watch).
"""
import json
import sys
from pathlib import Path

import numpy as np
from statsmodels.stats.multitest import multipletests

import ndvi  # reutiliza la sesión de AppEEARS (credenciales y token)
from tendencias import clasificar, estadisticas

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "pipeline" / "cache" / "cobertura"  # pipeline/cache/ está en .gitignore
TASK = CACHE / "task.json"
SALIDA = RAIZ / "data" / "cobertura_arboles.json"
APPEEARS = ndvi.APPEEARS

FUENTE = "MODIS MOD44B v061 (NASA LP DAAC) vía AppEEARS"
ANIOS = range(2001, 2025)  # mismo periodo que el resto del producto
BOSQUE = 30  # % de cobertura de árboles desde el que un píxel cuenta como bosque
MIN_FRAC_PIXELES = 0.5  # un año vale si tiene dato al menos la mitad del área de tierra
CAPA = "Percent_Tree_Cover"  # 0–100 %; 200 = agua; 253 = sin dato

ZONAS = [  # (id, nombre, departamento, ubigeo, tipo, (oeste, sur, este, norte))
    ("la-pampa", "La Pampa (Tambopata)", "Madre de Dios", "17", "selva con minería de oro",
     (-70.125, -13.0875, -69.875, -12.8375)),
    ("iquitos", "Selva cerca de Iquitos", "Loreto", "16", "selva", (-73.70, -4.20, -73.50, -4.00)),
]
UNIDAD_GEO = "recuadro de {lado} sobre la selva; no es el promedio del departamento"
# Aviso por zona (va en stats.aviso, delante del aviso de lag1, y la ficha lo muestra). El umbral NO
# cambia (decisión de Favio, 2026-11-15): La Pampa sigue posible_casualidad, pero se explica por qué.
# Los números salen de la serie, no del texto: al regenerar con un año nuevo el aviso no queda viejo.
# El 2009 solo describe lo que se ve; no es un corte con el que se calcule nada.
def aviso_la_pampa(serie):
    antes = [p["arboles_pct"] for p in serie if p["anio"] < 2009]
    ultimo = serie[-1]
    return (f"La pérdida no fue pareja: de {serie[0]['anio']} a 2008 la cobertura se mantuvo cerca del "
            f"{round(sum(antes) / len(antes))} % y desde 2009 baja casi cada año, hasta "
            f"{round(ultimo['arboles_pct'])} % en {ultimo['anio']}. La caída es grande y su rango "
            "probable no incluye 0, pero como empezó de golpe una recta la describe mal, y el "
            "criterio único no la marca como cambio real.")


AVISOS = {"la-pampa": aviso_la_pampa}


def unidad_geo(caja):
    o, s, e, n = caja
    lado = f"{e - o:.2f}° × {n - s:.2f}° (~{(e - o) * 111:.0f} × {(n - s) * 111:.0f} km)".replace(".", ",")
    return UNIDAD_GEO.format(lado=lado)


# ---------- lógica (sin red ni NetCDF: se prueba en autoprueba) ----------

def km_por_grado(lats):
    """(km por grado de latitud, km por grado de longitud) en cada latitud, en el elipsoide WGS84.

    Cerca del ecuador un grado de latitud mide ~110,6 km (no 111,32, que es el de longitud en el
    ecuador); usar el mismo valor para los dos inflaba el área ~0,7 %.
    """
    f = np.radians(lats)
    lat = 111.13295 - 0.55982 * np.cos(2 * f) + 0.00117 * np.cos(4 * f)
    lon = 111.41284 * np.cos(f) - 0.09350 * np.cos(3 * f) + 0.00012 * np.cos(5 * f)
    return lat, lon


def km2_pixeles(lats, dlat, dlon):
    """Área (km²) de un píxel en cada fila de latitud de una malla en grados.

    AppEEARS entrega el ráster en proyección geográfica: el píxel se encoge con la latitud, así que
    un área constante inflaría los km². Se usa el largo real de cada grado (km_por_grado).
    """
    km_lat, km_lon = km_por_grado(lats)
    return (abs(dlat) * km_lat) * (abs(dlon) * km_lon)


def resumen_anio(valores, tierra, area):
    """(fracción de tierra con dato, % de árboles medio, km² de bosque) de un año.

    valores: % de árboles por píxel (NaN = sin dato); tierra: máscara de píxeles de tierra;
    area: km² de cada píxel. El bosque se extrapola a toda la tierra según la fracción con dato
    (por área), para que un año con huecos no meta un escalón falso en la serie de km².
    """
    ok = tierra & ~np.isnan(valores)
    area_tierra = float(area[tierra].sum())
    area_ok = float(area[ok].sum())
    if area_ok == 0:
        return 0.0, float("nan"), 0.0
    bosque = float(area[ok & (valores >= BOSQUE)].sum())
    return area_ok / area_tierra, float(valores[ok].mean()), bosque * area_tierra / area_ok


def anual(por_anio):
    """Serie anual con solo años válidos (reglas-datos.md §1: MOD44B ya es un producto anual).

    por_anio: {anio: (fraccion_de_tierra_con_dato, arboles_pct_medio, km2_de_bosque)}.
    Devuelve {anio: {"arboles_pct", "area_bosque_km2"}} solo para años de ANIOS con dato en la
    mitad o más del área de tierra.
    """
    return {
        a: {"arboles_pct": round(pct, 2), "area_bosque_km2": round(km2, 1)}
        for a, (frac, pct, km2) in sorted(por_anio.items())
        if a in ANIOS and frac >= MIN_FRAC_PIXELES
    }


def zona_json(zona, pixeles, serie):
    """Fila de data/cobertura_arboles.json. `stats` (sobre arboles_pct) aún sin q_value ni status."""
    zid, nombre, depto, ubigeo, tipo, (o, s, e, n) = zona
    anios = np.array(sorted(serie))
    y = np.array([serie[a]["arboles_pct"] for a in anios], dtype=float)
    if len(y) < 3:
        # Con menos de 3 años no hay pendiente ni intervalo, y Stats (src/models/zona.rs) exige esos
        # campos: publicar la zona haría que la API no arranque. Mejor fallar aquí, con el motivo.
        raise ValueError(f"{nombre}: solo {len(y)} años válidos; con menos de 3 no hay tendencia "
                         "y no se publica. Revisa la descarga de AppEEARS.")
    st = estadisticas(anios, y, porcentaje=False)
    return {
        "id": zid, "nombre": nombre, "departamento": depto, "ubigeo": ubigeo, "tipo": tipo,
        "unidad_geografica": unidad_geo((o, s, e, n)), "bbox": [o, s, e, n],
        "lat": round((s + n) / 2, 3), "lon": round((o + e) / 2, 3),
        "pixeles": pixeles, "fuente": FUENTE, "umbral_bosque_pct": BOSQUE,
        "tendencia_de": "arboles_pct",
        "serie": [{"anio": int(a), **v} for a, v in sorted(serie.items())],
        "stats": st,
    }


def con_estado(filas):
    """q_value (BH entre las zonas del archivo), status y aviso con clasificar() de tendencias.py."""
    con_p = [f for f in filas if "p_value" in f["stats"]]
    qs = multipletests([f["stats"]["p_value"] for f in con_p], method="fdr_bh")[1] if con_p else []
    for f, q in zip(con_p, qs):
        aviso = AVISOS.get(f["id"])
        clasificar(f["stats"], q, f["pixeles"], aviso and aviso(f["serie"]))
    for f in filas:
        if "p_value" not in f["stats"]:
            f["stats"]["status"] = "pocos_datos"
    return filas


def escribir(filas, ruta=SALIDA):
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")


# ---------- AppEEARS (red) ----------

def enviar():
    import requests
    feats = [{"type": "Feature", "properties": {"id": z[0]},
              "geometry": {"type": "Polygon", "coordinates": [[[o, s], [e, s], [e, n], [o, n], [o, s]]]}}
             for z in ZONAS for (o, s, e, n) in [z[5]]]
    tarea = {"task_type": "area", "task_name": "detective-peru-cobertura-arboles",
             "params": {"dates": [{"startDate": f"01-01-{ANIOS[0]}", "endDate": f"12-31-{ANIOS[-1]}"}],
                        "layers": [{"product": "MOD44B.061", "layer": CAPA}],
                        "geo": {"type": "FeatureCollection", "features": feats},
                        "output": {"format": {"type": "netcdf4"}, "projection": "geographic"}}}
    r = requests.post(f"{APPEEARS}/task", json=tarea, headers=ndvi._token(), timeout=120)
    r.raise_for_status()
    CACHE.mkdir(parents=True, exist_ok=True)
    TASK.write_text(json.dumps(r.json()))
    print("solicitud creada:", r.json()["task_id"])


def _estado(h):
    import requests
    tid = json.loads(TASK.read_text())["task_id"]
    r = requests.get(f"{APPEEARS}/task/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    return tid, r.json().get("status")


def consultar():
    print(_estado(ndvi._token())[1])


def bajar():
    import requests
    h = ndvi._token()
    tid, estado = _estado(h)
    if estado != "done":
        sys.exit(f"La solicitud aún no termina (estado: {estado}). Prueba más tarde con `estado`.")
    r = requests.get(f"{APPEEARS}/bundle/{tid}", headers=h, timeout=60)
    r.raise_for_status()
    # Se baja todo a .part y solo al final se reemplazan los .nc: si la descarga se corta,
    # la copia buena anterior sigue ahí (repetir la solicitud a AppEEARS cuesta horas).
    for viejo in CACHE.glob("*.part"):  # restos de una corrida que murió sin poder limpiar
        viejo.unlink()
    nuevos = []
    parcial = None  # el .part que se está escribiendo (se limpia también si falla a medias)
    try:
        for f in r.json()["files"]:
            if not f["file_name"].endswith(".nc"):
                continue
            destino = CACHE / Path(f["file_name"]).name
            parcial = destino.with_name(destino.name + ".part")
            with requests.get(f"{APPEEARS}/bundle/{tid}/{f['file_id']}", headers=h, stream=True,
                              timeout=600) as d:
                d.raise_for_status()
                with open(parcial, "wb") as fh:
                    for trozo in d.iter_content(1 << 20):
                        fh.write(trozo)
            nuevos.append((parcial, destino))
            print(destino.name, f"{parcial.stat().st_size / 1e6:.1f} MB")
            parcial = None
    except BaseException:
        for p in [*(p for p, _ in nuevos), parcial]:
            if p is not None:
                p.unlink(missing_ok=True)
        raise
    if not nuevos:
        # Sin ningún .nc en el bundle no se toca la caché: la copia buena anterior sigue
        sys.exit("El bundle de AppEEARS no trae ningún .nc; se conserva la copia anterior.")
    finales = {d for _, d in nuevos}
    for viejo in CACHE.glob("*.nc"):
        if viejo not in finales:
            viejo.unlink()
    for parcial, destino in nuevos:
        parcial.replace(destino)


# ---------- NetCDF -> data/cobertura_arboles.json ----------

def _leer_zona(zona):
    """NetCDF cuyo centro cae en la caja de la zona -> (pixeles_de_tierra, {anio: (frac, pct, km2)})."""
    import xarray as xr
    o, s, e, n = zona[5]
    candidatos = []
    for ruta in sorted(CACHE.glob("*.nc")):
        with xr.open_dataset(ruta) as ds:
            if o <= float(ds.lon.mean()) <= e and s <= float(ds.lat.mean()) <= n:
                candidatos.append(ruta)
    if len(candidatos) != 1:
        sys.exit(f"{zona[1]}: {len(candidatos)} NetCDF en {CACHE} (se espera 1). Corre `bajar` de nuevo.")
    with xr.open_dataset(candidatos[0], mask_and_scale=False) as ds:
        v = ds[CAPA].values.astype(float)  # (tiempo, lat, lon)
        anios = [int(a) for a in ds["time"].dt.year.values]  # .dt sirve con datetime64 y cftime
        lats, lons = ds["lat"].values, ds["lon"].values
    area = np.repeat(
        km2_pixeles(lats, np.diff(lats).mean(), np.diff(lons).mean())[:, None], len(lons), axis=1)
    valido = (v >= 0) & (v <= 100)  # fuera: 200 (agua) y 253 (sin dato)
    agua = (v == 200).all(axis=0)
    tierra = ~agua & valido.any(axis=0)  # píxeles de tierra con algún año con dato
    por_anio = {}
    for i, a in enumerate(anios):
        if valido[i].any():
            por_anio[a] = resumen_anio(np.where(valido[i], v[i], np.nan), tierra, area)
    return int(tierra.sum()), por_anio


def calcular():
    filas = []
    for zona in ZONAS:
        pixeles, por_anio = _leer_zona(zona)
        serie = anual(por_anio)
        if len(serie) < len(ANIOS):
            print(f"aviso: {zona[1]} tiene {len(serie)} de {len(ANIOS)} años")
        filas.append(zona_json(zona, pixeles, serie))
    escribir(con_estado(filas))
    for f in filas:
        st, a = f["stats"], {str(p["anio"]): p for p in f["serie"]}
        ext = " · ".join(f"{k}: {a[k]['arboles_pct']} % árboles, {a[k]['area_bosque_km2']} km² de bosque"
                         for k in (min(a, default=""), max(a, default="")) if k in a)
        print(f"{f['nombre']}: {st['n_years']} años, Sen {st.get('slope_per_decade', 0):+.3f} pp/déc "
              f"IC [{st.get('ci_low')}, {st.get('ci_high')}], {st['status']} · {ext}")


def autoprueba():
    # Años: entra 2001; no entran 2002 (menos de la mitad de píxeles) ni 2000 y 2025 (fuera de 2001–2024).
    serie = anual({2000: (1.0, 80.0, 500.0), 2001: (0.9, 80.0, 500.0), 2002: (0.4, 80.0, 500.0),
                   2025: (1.0, 80.0, 500.0)})
    assert serie == {2001: {"arboles_pct": 80.0, "area_bosque_km2": 500.0}}, serie

    azar = np.random.default_rng(2)

    def zona(pendiente, ruido, anios=ANIOS):
        return {a: {"arboles_pct": float(80 + pendiente * (a - 2001) + azar.normal(0, ruido)),
                    "area_bosque_km2": 500.0} for a in anios}

    filas = con_estado([
        zona_json(ZONAS[0], 12000, zona(-0.8, 0.5)),                       # pierde bosque: real
        zona_json(ZONAS[1], 9000, zona(0.0, 0.5)),                         # sin cambio: posible_casualidad
        zona_json(ZONAS[1], 9000, zona(-0.8, 0.5, range(2001, 2013))),     # 12 años: pocos_datos
    ])
    estados = [f["stats"]["status"] for f in filas]
    assert estados == ["real", "posible_casualidad", "pocos_datos"], estados
    assert all({"year_start", "year_end", "slope_per_decade", "ci_low", "q_value"} <= set(f["stats"])
               for f in filas), "todos los status con el esquema completo de Stats"
    for pocos in ({}, zona(-0.8, 0.5, range(2001, 2003))):  # 0 y 2 años: no se publican
        try:
            zona_json(ZONAS[1], 9000, pocos)
            raise AssertionError("una zona con menos de 3 años no debe publicarse")
        except ValueError:
            pass

    # Área: el recuadro de Iquitos (0,2° × 0,2°) contra una fórmula independiente, la de la zona
    # esférica con el radio de igual área de la Tierra: R² · Δλ · (sen φ2 − sen φ1) ≈ 491 km²
    lats = np.arange(-4.199, -4.0, 0.002)
    caja = km2_pixeles(lats, 0.002, 0.002).sum() * 100
    esfera = 6371.0072 ** 2 * np.radians(0.2) * (np.sin(np.radians(-4.0)) - np.sin(np.radians(-4.2)))
    assert abs(caja / esfera - 1) < 0.005, (caja, esfera)
    km_lat, km_lon = km_por_grado(np.array([0.0]))
    assert abs(km_lat[0] - 110.57) < 0.01 and abs(km_lon[0] - 111.32) < 0.01, (km_lat, km_lon)
    # Un año con la mitad de la tierra sin dato da el mismo bosque (extrapolado), sin escalón
    area = np.ones((4, 4))
    tierra = np.ones((4, 4), bool)
    lleno = np.full((4, 4), 80.0)
    medio = lleno.copy()
    medio[:2] = np.nan
    assert resumen_anio(lleno, tierra, area) == (1.0, 80.0, 16.0)
    assert resumen_anio(medio, tierra, area) == (0.5, 80.0, 16.0)
    assert filas[0]["stats"]["slope_per_decade"] < 0
    # La Pampa lleva su aviso aunque salga real; Iquitos no lleva aviso propio
    ultimo = filas[0]["serie"][-1]
    assert f"hasta {round(ultimo['arboles_pct'])} % en {ultimo['anio']}" in filas[0]["stats"]["aviso"], filas[0]["stats"]
    assert "aviso" not in filas[1]["stats"] or "2009" not in filas[1]["stats"]["aviso"]
    texto = json.dumps(filas, allow_nan=False)
    assert "NaN" not in texto and "null" not in texto
    assert filas[0]["ubigeo"] == "17" and "no es el promedio del departamento" in filas[0]["unidad_geografica"]
    print("autoprueba cobertura OK")


if __name__ == "__main__":
    acciones = {"enviar": enviar, "estado": consultar, "bajar": bajar, "calcular": calcular, "autoprueba": autoprueba}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        sys.exit(f"uso: python pipeline/cobertura.py {{{'|'.join(acciones)}}}")
    acciones[sys.argv[1]]()
