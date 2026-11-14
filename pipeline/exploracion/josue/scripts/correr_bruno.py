"""Ejecuta las peticiones de la colección de Bruno *Detective Josue* (formato OpenCollection YAML).

Por qué existe: el CLI oficial (`@usebruno/cli`) no se pudo instalar en esta máquina
(registro de npm inaccesible desde el entorno). Este runner lee los mismos .yml,
sustituye las variables {{...}} del environment `Peru` y lanza la misma petición.
Las peticiones que necesitan credenciales (auth basic o tokens) se saltan si no hay
variables secretas definidas en el entorno del proceso (EDL_USER / EDL_PASS).

Salida: salida/bruno_resultados.json y salida/bruno_resultados.md
Uso:    .venv/bin/python scripts/correr_bruno.py [ruta_coleccion]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml

RAIZ = Path(__file__).resolve().parent.parent
COL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "bruno" / "Detective Josue"


def variables():
    env = yaml.safe_load((COL / "environments" / "Peru.yml").read_text())
    v = {x["name"]: x.get("value", "") for x in env["variables"] if not x.get("secret")}
    v["edl_user"], v["edl_pass"] = os.environ.get("EDL_USER", ""), os.environ.get("EDL_PASS", "")
    return v


def sustituir(texto, v):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(v.get(m.group(1), m.group(0))), texto)


def resumen_cuerpo(nombre, cuerpo):
    """Extrae lo que el docs de cada petición dice que hay que mirar."""
    if isinstance(cuerpo, dict) and "properties" in cuerpo:  # POWER punto
        par = cuerpo["properties"]["parameter"]
        meses = {k for k in next(iter(par.values())) if not k.endswith("13")}
        falt = {k: sum(1 for m, x in s.items() if not m.endswith("13") and x == -999) for k, s in par.items()}
        return {"variables": sorted(par), "meses": len(meses), "faltantes_-999": falt,
                "unidades": {k: x.get("units") for k, x in cuerpo.get("parameters", {}).items()}}
    if isinstance(cuerpo, dict) and "features" in cuerpo:  # POWER regional
        f = cuerpo["features"]
        return {"celdas": len(f), "mensajes": cuerpo.get("messages")}
    if isinstance(cuerpo, dict) and "_1_km_monthly_NDVI" in cuerpo:  # AppEEARS capas
        ndvi = cuerpo["_1_km_monthly_NDVI"]
        return {"capas": sorted(cuerpo), "NDVI": {k: ndvi.get(k) for k in ("ScaleFactor", "FillValue", "ValidMin", "ValidMax", "Units")}}
    return {"tipo": type(cuerpo).__name__}


def main():
    v = variables()
    resultados = []
    for f in sorted(COL.rglob("*.yml")):
        if f.name == "opencollection.yml" or "environments" in f.parts:
            continue
        req = yaml.safe_load(f.read_text())
        http = req["http"]
        nombre = f"{f.parent.name}/{req['info']['name']}"
        auth = http.get("auth")
        usa_secreto = (isinstance(auth, dict) and auth.get("type") == "basic") or "token}}" in json.dumps(http)
        if usa_secreto and not (v["edl_user"] and v["edl_pass"]):
            resultados.append({"peticion": nombre, "estado": "saltada", "motivo": "requiere credencial Earthdata"})
            continue
        url = sustituir(http["url"], v)
        headers = {h["name"]: sustituir(h["value"], v) for h in http.get("headers", [])}
        kw = {"headers": headers, "timeout": 300}
        if isinstance(auth, dict) and auth.get("type") == "basic":
            kw["auth"] = (sustituir(auth["username"], v), sustituir(auth["password"], v))
        t = time.time()
        r = requests.request(http["method"], url, **kw)
        seg = time.time() - t
        fila = {"peticion": nombre, "metodo": http["method"], "http": r.status_code,
                "segundos": round(seg, 2), "kb": round(len(r.content) / 1024, 1)}
        try:
            fila["resumen"] = resumen_cuerpo(nombre, r.json())
        except ValueError:
            fila["resumen"] = {"texto": r.text[:120]}
        fila["estado"] = "ok" if r.ok else "error"
        resultados.append(fila)
        print(f"{fila['estado']:6} {r.status_code} {seg:5.1f}s {fila['kb']:>8} KB  {nombre}")
    (RAIZ / "salida" / "bruno_resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    with open(RAIZ / "salida" / "bruno_resultados.md", "w") as fh:
        fh.write("| Petición | HTTP | Tiempo (s) | Tamaño (KB) | Estado |\n|---|---|---|---|---|\n")
        for x in resultados:
            fh.write(f"| {x['peticion']} | {x.get('http', '—')} | {x.get('segundos', '—')} | {x.get('kb', '—')} | "
                     f"{x['estado']}{' (' + x['motivo'] + ')' if 'motivo' in x else ''} |\n")


if __name__ == "__main__":
    main()
