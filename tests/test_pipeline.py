"""Pruebas de los avisos y del modo incremental del pipeline (sin red)."""
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import gpm  # noqa: E402
import power  # noqa: E402

DATOS = Path(__file__).resolve().parent.parent / "data"


class Incremental(unittest.TestCase):
    def test_gpm_json_actual_se_reusa_completo(self):
        filas = json.loads((DATOS / "gpm.json").read_text(encoding="utf-8"))
        anios, celdas = gpm.guardados(filas)
        self.assertEqual(sorted(anios), [str(a) for a in range(2001, 2025)])
        self.assertEqual(len(anios["2010"]), 25)
        self.assertEqual(celdas["Amazonas"], filas[0]["celdas"])

    def test_anio_que_falta_en_una_region_se_vuelve_a_pedir(self):
        filas = json.loads((DATOS / "gpm.json").read_text(encoding="utf-8"))
        del filas[3]["anios"]["2010"]
        anios, _ = gpm.guardados(filas)
        self.assertNotIn("2010", anios)
        self.assertIn("2011", anios)

    def test_json_incompleto_no_se_reusa(self):
        self.assertEqual(gpm.guardados([]), ({}, {}))


class Avisos(unittest.TestCase):
    def test_power_avisa_anios_descartados(self):
        salida = io.StringIO()
        power.avisar_incompletos({2026: list(power.REGIONES), 2003: ["Callao"]}, salida)
        lineas = salida.getvalue().splitlines()
        self.assertEqual(lineas, ["AVISO 2003: sin 12 meses en Callao; ese año no entra",
                                  "AVISO 2026: sin 12 meses en 25 regiones; ese año no entra"])


if __name__ == "__main__":
    unittest.main()
