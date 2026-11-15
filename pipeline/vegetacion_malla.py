"""Malla de vegetación (NDVI anual) de todo el Perú a 0,25° -> data/celdas/vegetacion.json.

Fuente: MODIS MOD13A3 v061 (NASA LP DAAC), NDVI mensual a 1 km, pedido a AppEEARS (el mismo
producto y las mismas capas que pipeline/ndvi.py, el del Caso 2).

Uso (desde la raíz del repo):
  python pipeline/vegetacion_malla.py enviar      crea 4 solicitudes en AppEEARS (6 años cada una)
  python pipeline/vegetacion_malla.py estado      estado de las 4 solicitudes
  python pipeline/vegetacion_malla.py bajar       descarga los NetCDF a pipeline/cache/vegetacion/<bloque>/
  python pipeline/vegetacion_malla.py calcular    NetCDF -> data/celdas/vegetacion.json + tabla por región
  python pipeline/vegetacion_malla.py autoprueba  prueba la lógica sin red ni NetCDF (la corre tests/e2e.sh)

Se pide en 4 bloques de años porque una sola solicitud de todo el país y 24 años pesa varios GB y
AppEEARS la procesa más lento; cada bloque va a su propia carpeta de caché (appeears.bajar borra los
.nc que no son de su solicitud).

Método, por píxel de 1 km:
  1. un mes vale si el píxel es confiable (pixel_reliability 0 o 1, igual que ndvi.py): así se
     quitan nubes, nieve y agua;
  2. NDVI anual del píxel = media de sus meses confiables, solo si tiene al menos MIN_MESES;
  3. NDVI de la celda de 0,25° = media de los píxeles con año válido, solo si son al menos
     MIN_FRAC_PIXELES de los píxeles con dato de la celda; si no, null ese año.
La tarea pedía 12 meses con dato. En la selva y los Andes las nubes tapan casi siempre algún mes
del año en algún píxel; exigir 12 de 12 por píxel dejaría la selva vacía. Por eso se exige
MIN_MESES por píxel y se avisa en la `nota` del archivo.

Refresco: a mano, una vez al año (enero), no en el cron: AppEEARS tarda horas.
"""
import json
import sys
from pathlib import Path

import numpy as np

import appeears

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "pipeline" / "cache" / "vegetacion"  # en .gitignore (pipeline/cache/)
SALIDA = RAIZ / "data" / "celdas" / "vegetacion.json"
SALIDA_DEPTOS = RAIZ / "data" / "ndvi_departamentos.json"  # fuente de zonas/vegetacion.json (tendencias.py)
PRODUCTO = "MOD13A3.061"
CAPAS = ["_1_km_monthly_NDVI", "_1_km_monthly_pixel_reliability"]
FUENTE = "MODIS MOD13A3 v061 (NDVI) vía AppEEARS"

ANIOS = range(2001, 2025)
BLOQUES = [range(2001, 2007), range(2007, 2013), range(2013, 2019), range(2019, 2025)]
# Recuadro que cubre todo el Perú (oeste, sur, este, norte); la máscara de departamentos recorta
CAJA_PERU = (-81.5, -18.5, -68.5, 0.1)
PASO = 0.25  # grados por lado de la celda
MIN_MESES = 6  # meses confiables por píxel para que su año cuente
MIN_FRAC_PIXELES = 0.5  # fracción de píxeles con año válido para que la celda tenga ese año
MIN_ANIOS_REGION = 15  # una celda "cuenta" para la cobertura si tiene dato en 15 años o más
MIN_ANIOS_TENDENCIA = 20  # = tendencias.MIN_ANIOS (no se importa: arrastra scipy a la autoprueba)
NOTA = (f"NDVI anual = media de los meses sin nubes de cada píxel de 1 km (mínimo {MIN_MESES} meses), "
        f"promediada a celdas de {PASO}°. En la selva el NDVI se satura (~0,8–0,9): sirve para ver dónde hay "
        "vegetación, no para medir cambios de bosque (ver /api/cobertura-arboles).")


def _task(bloque):
    return CACHE / f"{bloque[0]}-{bloque[-1]}" / "task.json"


def _dir(bloque):
    return CACHE / f"{bloque[0]}-{bloque[-1]}"


# ---------- lógica (sin red ni NetCDF: se prueba en autoprueba) ----------

def centros(inicio, fin, paso=PASO):
    """Centros de las celdas de `paso` grados alineadas a múltiplos de `paso` entre inicio y fin."""
    a = np.floor(inicio / paso) * paso
    return np.round(np.arange(a + paso / 2, fin, paso), 4)


def anual_pixel(ndvi, fiable, min_meses=MIN_MESES):
    """(meses, lat, lon) de un año -> NDVI anual por píxel (NaN si tiene menos de min_meses buenos)."""
    bueno = np.isin(fiable, [0, 1]) & np.isfinite(ndvi)
    n = bueno.sum(axis=0)
    suma = np.where(bueno, ndvi, 0.0).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        media = suma / n
    return np.where(n >= min_meses, media, np.nan), n > 0


def a_celdas(anual, con_dato, lat, lon, paso=PASO, min_frac=MIN_FRAC_PIXELES):
    """NDVI anual por píxel (lat, lon) -> {(lat_c, lon_c): valor} por celda de `paso` grados.

    `con_dato`: píxeles que alguna vez tienen dato (fuera del mar y del recorte); la fracción
    mínima se mide sobre ellos, así una celda de costa no queda vacía por el mar."""
    ui, fi = np.unique(np.floor(lat / paso).astype(int), return_inverse=True)
    uj, fj = np.unique(np.floor(lon / paso).astype(int), return_inverse=True)
    celda = fi[:, None] * len(uj) + fj[None, :]  # índice de celda de cada píxel
    n = len(ui) * len(uj)
    total = np.bincount(celda[con_dato], minlength=n)
    bueno = con_dato & np.isfinite(anual)
    cuenta = np.bincount(celda[bueno], minlength=n)
    suma = np.bincount(celda[bueno], weights=anual[bueno], minlength=n)
    salida = {}
    for k in np.flatnonzero((total > 0) & (cuenta > 0) & (cuenta >= min_frac * total)):
        ci, cj = ui[k // len(uj)], uj[k % len(uj)]
        salida[(round(float(ci + 0.5) * paso, 4), round(float(cj + 0.5) * paso, 4))] = float(suma[k] / cuenta[k])
    return salida


def anios_de(valores, unidades):
    """Año de cada tiempo de AppEEARS: unidades "seconds since 2000-01-01 ..." o "days since ..."."""
    paso, base = unidades.split(" since ")
    escala = {"seconds": "s", "days": "D", "hours": "h"}[paso.strip()]
    fechas = np.datetime64(base.strip()[:10]) + np.asarray(valores).astype(f"timedelta64[{escala}]")
    return fechas.astype("datetime64[Y]").astype(int) + 1970


def malla_json(por_anio, dentro, anios=ANIOS):
    """{anio: {(lat, lon): ndvi}} + {(lat, lon): region} -> dict de data/celdas/vegetacion.json.
    Solo celdas dentro de Perú y con al menos un año; null si falta el año; 3 decimales."""
    claves = sorted({c for d in por_anio.values() for c in d if c in dentro}, key=lambda c: (-c[0], c[1]))
    celdas = []
    for c in claves:
        valor = [None if (v := por_anio.get(a, {}).get(c)) is None else round(v, 3) for a in anios]
        if any(v is not None for v in valor):
            celdas.append({"lat": c[0], "lon": c[1], "valor": valor})
    return {
        "fuente": FUENTE, "unidad": "NDVI", "nota": NOTA,
        "dlat": PASO, "dlon": PASO, "anio_inicio": anios[0], "anio_fin": anios[-1],
        "celdas": celdas,
    }


def por_departamento(malla, dentro, regiones, capitales):
    """NDVI anual de cada región = media de sus celdas, solo los años en que al menos la mitad de sus
    celdas tienen dato. Callao (sin celdas propias): la celda más cercana a su capital, con nota.
    Devuelve (datos {region: {"AAAA": {"ndvi": x}}}, celdas {region: n}, notas {region: texto})."""
    anios = range(malla["anio_inicio"], malla["anio_fin"] + 1)
    por_reg = {r: [] for r in regiones}
    for c in malla["celdas"]:
        por_reg[regiones[dentro[(c["lat"], c["lon"])]]].append(c)
    datos, celdas, notas = {}, {}, {}
    for r, propias in por_reg.items():
        celdas[r] = len(propias)
        if not propias:
            lat, lon = capitales[r]
            propias = [min(malla["celdas"], key=lambda c: (c["lat"] - lat) ** 2 + (c["lon"] - lon) ** 2)]
            notas[r] = f"Sin celdas propias de {PASO}°: se usa la celda más cercana a su capital"
        if len(anios) < MIN_ANIOS_TENDENCIA:
            # pocos_datos por la serie corta, no por las celdas: la nota dice el motivo real
            corta = (f"Serie de solo {len(anios)} años ({anios[0]}–{anios[-1]}): hacen falta "
                     f"{MIN_ANIOS_TENDENCIA} para medir una tendencia")
            notas[r] = f"{notas[r]}. {corta}" if r in notas else corta
        datos[r] = {}
        for k, a in enumerate(anios):
            vals = [c["valor"][k] for c in propias if c["valor"][k] is not None]
            if vals and len(vals) * 2 >= len(propias):
                datos[r][str(a)] = {"ndvi": round(sum(vals) / len(vals), 4)}
    return datos, celdas, notas


def cobertura(malla, dentro, regiones, min_anios=MIN_ANIOS_REGION):
    """{region: (celdas con >= min_anios años, NDVI medio de esas celdas)}."""
    por_reg = {r: [] for r in regiones}
    for c in malla["celdas"]:
        vals = [v for v in c["valor"] if v is not None]
        if len(vals) >= min_anios:
            por_reg[regiones[dentro[(c["lat"], c["lon"])]]].append(sum(vals) / len(vals))
    return {r: (len(v), round(sum(v) / len(v), 3) if v else None) for r, v in por_reg.items()}


# ---------- AppEEARS (red): pipeline/appeears.py ----------

def enviar():
    zona = ("peru", "Perú", "", "", "país", CAJA_PERU)
    for b in BLOQUES:
        if _task(b).exists():
            print(f"{b[0]}-{b[-1]}: ya hay solicitud ({_task(b)}); bórrala para pedir de nuevo")
            continue
        appeears.enviar([zona], PRODUCTO, CAPAS, b, _task(b), f"detective-peru-vegetacion-{b[0]}-{b[-1]}")


def consultar():
    h = appeears.token()
    for b in BLOQUES:
        print(f"{b[0]}-{b[-1]}:", appeears.estado(h, _task(b))[1] if _task(b).exists() else "sin solicitud")


def bajar():
    for b in BLOQUES:
        print(f"== {b[0]}-{b[-1]}")
        appeears.bajar(_task(b), _dir(b))


# ---------- NetCDF -> data/celdas/vegetacion.json ----------

def _leer_bloque(b):
    """{anio: {(lat_c, lon_c): ndvi}} de un bloque. Lee año por año para no cargar GB en memoria."""
    import xarray as xr
    rutas = sorted(_dir(b).glob("*.nc"))
    if len(rutas) != 1:
        sys.exit(f"{b[0]}-{b[-1]}: {len(rutas)} NetCDF en {_dir(b)} (se espera 1). Corre `bajar`.")
    # decode_times=False: el calendario juliano de AppEEARS pide cftime; el año sale de las unidades
    with xr.open_dataset(rutas[0], decode_times=False) as ds:
        lat, lon = ds["lat"].values, ds["lon"].values
        t = ds["time"]
        anios = anios_de(t.values, t.attrs["units"])
        con_dato = np.zeros((lat.size, lon.size), bool)
        por_anio = {}
        for a in b:
            idx = np.nonzero(anios == a)[0]
            if not idx.size:
                continue
            ndvi = ds[CAPAS[0]].isel(time=idx).values
            fiable = ds[CAPAS[1]].isel(time=idx).values
            anual, alguno = anual_pixel(ndvi, fiable)
            con_dato |= alguno
            por_anio[a] = (anual, len(idx))
        out = {}
        for a, (anual, meses) in por_anio.items():
            if meses < 12:
                print(f"aviso: {a} trae {meses} meses en AppEEARS")
            out[a] = a_celdas(anual, con_dato, lat, lon)
    return out


def calcular():
    from departamentos import mascara
    from power import REGIONES

    por_anio = {}
    for b in BLOQUES:
        if not any(_dir(b).glob("*.nc")):
            # Un bloque que AppEEARS aún no entregó no se inventa: la malla llega hasta el último año leído
            print(f"AVISO {b[0]}-{b[-1]}: sin NetCDF todavía (corre `estado` y `bajar`); queda fuera", flush=True)
            continue
        por_anio.update(_leer_bloque(b))
        print(f"{b[0]}-{b[-1]} leído", flush=True)
    if not por_anio:
        sys.exit("No hay ningún bloque descargado.")
    anios = range(min(por_anio), max(por_anio) + 1)
    if len(anios) < len(ANIOS):
        print(f"AVISO: malla parcial {anios[0]}–{anios[-1]} (faltan bloques de AppEEARS)", flush=True)
    lats, lons = centros(CAJA_PERU[1], CAJA_PERU[3]), centros(CAJA_PERU[0], CAJA_PERU[2])
    masc = mascara(lats, lons)
    dentro = {(float(lats[i]), float(lons[j])): int(masc[i, j])
              for i, j in zip(*np.nonzero(np.isfinite(masc)))}
    malla = malla_json(por_anio, dentro, anios)
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(malla, ensure_ascii=False, allow_nan=False, separators=(",", ":")),
                      encoding="utf-8")
    print(f"{len(malla['celdas'])} celdas -> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size / 1e3:.0f} KB)")
    # Con una malla parcial, «con dato en 15 años o más» se vuelve «en todos los años leídos»
    min_anios = min(MIN_ANIOS_REGION, len(anios))
    tabla(cobertura(malla, dentro, list(REGIONES), min_anios), min_anios)
    from departamentos import a_json
    import tendencias
    datos, celdas, notas = por_departamento(malla, dentro, list(REGIONES), REGIONES)
    tendencias.escribir(SALIDA_DEPTOS, a_json(datos, celdas, notas))
    print(f"25 regiones -> {SALIDA_DEPTOS.relative_to(RAIZ)}; ahora corre: python pipeline/tendencias.py")


def tabla(cob, min_anios=MIN_ANIOS_REGION):
    print(f"\n| Región | Celdas (≥ {min_anios} años) | NDVI medio |\n|---|---|---|")
    for r, (n, m) in cob.items():
        marca = " ⚠️" if n < 4 else ""
        print(f"| {r} | {n}{marca} | {'—' if m is None else str(m).replace('.', ',')} |")


def autoprueba():
    # Celdas alineadas a 0,25°: el centro de -12,1 es -12,125
    assert list(centros(-12.25, -11.75)) == [-12.125, -11.875]
    # Un píxel con 6 meses buenos cuenta; con 5 no; el mes nuboso (fiable=3) no entra en la media
    ndvi = np.full((12, 1, 3), 0.5)
    fiable = np.zeros((12, 1, 3), int)
    fiable[:7, 0, 1] = 3  # píxel 1: solo 5 meses buenos
    fiable[0, 0, 2] = 3
    ndvi[0, 0, 2] = 0.9  # píxel 2: el mes nuboso tiene 0,9 y no debe pesar
    anual, alguno = anual_pixel(ndvi, fiable)
    assert anual[0, 0] == 0.5 and np.isnan(anual[0, 1]) and anual[0, 2] == 0.5, anual
    assert alguno.all()
    # Celda: 4 píxeles con dato, 2 válidos -> entra (50 %); con 1 válido -> null
    lat = np.array([-12.2, -12.1])
    lon = np.array([-77.2, -77.1])
    a = np.array([[0.2, 0.4], [np.nan, np.nan]])
    con = np.ones((2, 2), bool)
    assert abs(a_celdas(a, con, lat, lon)[(-12.125, -77.125)] - 0.3) < 1e-9
    a[0, 1] = np.nan
    assert a_celdas(a, con, lat, lon) == {}
    # El mar (sin dato nunca) no cuenta para la fracción
    con[0, 1] = con[1, :] = False
    assert a_celdas(a, con, lat, lon) == {(-12.125, -77.125): 0.2}
    # JSON: solo celdas dentro, null si falta el año, ninguna celda toda null, 3 decimales
    dentro = {(-12.125, -77.125): 14, (-3.625, -73.375): 15}
    por_anio = {2001: {(-12.125, -77.125): 0.12345, (-3.625, -73.375): 0.8, (5.0, 5.0): 0.5},
                2002: {(-3.625, -73.375): 0.81}}
    m = malla_json(por_anio, dentro, anios=range(2001, 2003))
    assert [c["valor"] for c in m["celdas"]] == [[0.8, 0.81], [0.123, None]], m["celdas"]
    assert m["unidad"] == "NDVI" and m["anio_fin"] == 2002 and m["dlat"] == PASO
    texto = json.dumps(m, allow_nan=False)
    assert "NaN" not in texto
    cob = cobertura(m, dentro, [f"r{i}" for i in range(14)] + ["Lima", "Loreto"], min_anios=2)
    assert cob["Loreto"] == (1, 0.805) and cob["Lima"] == (0, None), cob
    # Por departamento: año con la mitad de celdas entra; Callao sin celdas usa la más cercana
    regiones = [f"r{i}" for i in range(14)] + ["Lima", "Loreto", "Callao"]
    m2 = {"anio_inicio": 2001, "anio_fin": 2002, "celdas": [
        {"lat": -3.625, "lon": -73.375, "valor": [0.8, None]},
        {"lat": -3.875, "lon": -73.375, "valor": [0.6, 0.7]},
        {"lat": -12.125, "lon": -77.125, "valor": [0.1, None]}]}
    dentro2 = {(-3.625, -73.375): 15, (-3.875, -73.375): 15, (-12.125, -77.125): 14}
    datos, celdas, notas = por_departamento(m2, dentro2, regiones, dict.fromkeys(regiones, (-12.06, -77.13)))
    assert datos["Loreto"] == {"2001": {"ndvi": 0.7}, "2002": {"ndvi": 0.7}}, datos["Loreto"]
    assert datos["Lima"] == {"2001": {"ndvi": 0.1}} and celdas["Callao"] == 0
    assert datos["Callao"] == datos["Lima"] and "capital" in notas["Callao"]
    assert "solo 2 años" in notas["Loreto"] and "solo 2 años" in notas["Callao"]
    # Tiempo de AppEEARS: en segundos (MOD13A3 de 2026) o en días
    assert list(anios_de([0, 31_536_000 * 2], "seconds since 2000-01-01 00:00:00+00:00")) == [2000, 2001]
    assert list(anios_de([366, 400], "days since 2000-01-01")) == [2001, 2001]
    print("autoprueba vegetacion_malla OK")


if __name__ == "__main__":
    acciones = {"enviar": enviar, "estado": consultar, "bajar": bajar, "calcular": calcular,
                "autoprueba": autoprueba}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        sys.exit(f"uso: python pipeline/vegetacion_malla.py {{{'|'.join(acciones)}}}")
    acciones[sys.argv[1]]()
