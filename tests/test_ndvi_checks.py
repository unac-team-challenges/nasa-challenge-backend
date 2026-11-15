"""Los checks de data/ndvi.json (tests/checks_ndvi.sh) aceptan un archivo válido y detectan cada rotura.

Mientras data/ndvi.json no exista, el e2e no corre esos checks: esta prueba los mantiene probados
con un archivo de ejemplo hecho con las mismas funciones de pipeline/ndvi.py.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "pipeline"))

import numpy as np  # noqa: E402

import ndvi  # noqa: E402


def ejemplo():
    azar = np.random.default_rng(1)
    serie = lambda pendiente: {  # noqa: E731
        a: {"ndvi_anual": float(0.2 + pendiente * (a - 2001) + azar.normal(0, 0.005)), "area_verde_km2": 100.0}
        for a in ndvi.ANIOS}
    return ndvi.con_estado([ndvi.zona_json(ndvi.ZONAS[0], 847, serie(0.005)),
                            ndvi.zona_json(ndvi.ZONAS[1], 900, serie(0.0))])


ROTURAS = {
    "null en la serie": lambda f: f[0]["anios"]["2005"].update(ndvi_anual=None),
    "NaN en stats": lambda f: f[0]["stats"].update(q_value=float("nan")),
    "NDVI fuera de [-1, 1]": lambda f: f[0]["anios"]["2005"].update(ndvi_anual=1.4),
    "año fuera de 2001–2024": lambda f: f[0]["anios"].update({"2025": dict(f[0]["anios"]["2024"])}),
    "status inválido": lambda f: f[0]["stats"].update(status="tal_vez"),
    "'real' que no cumple el criterio": lambda f: f[1]["stats"].update(status="real", q_value=0.2),
    "sin unidad geográfica explícita": lambda f: f[0].update(unidad_geografica="departamento"),
}


def pasan(filas):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        t.write(json.dumps(filas))  # allow_nan por defecto: así se puede escribir la rotura NaN
    r = subprocess.run(["bash", str(RAIZ / "tests/checks_ndvi.sh"), t.name], capture_output=True, text=True)
    Path(t.name).unlink()
    return r.returncode == 0


class ChecksNdvi(unittest.TestCase):
    def test_ejemplo_valido_pasa(self):
        filas = ejemplo()
        self.assertEqual([f["stats"]["status"] for f in filas], ["real", "posible_casualidad"])
        self.assertTrue(pasan(filas))

    def test_cada_rotura_se_detecta(self):
        base = ejemplo()
        for nombre, romper in ROTURAS.items():
            with self.subTest(nombre):
                filas = copy.deepcopy(base)
                romper(filas)
                self.assertFalse(pasan(filas), f"los checks no detectaron: {nombre}")


if __name__ == "__main__":
    unittest.main()
