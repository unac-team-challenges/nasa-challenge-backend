"""Pruebas de pipeline/tendencias.py. Uso: python -m unittest tests/test_tendencias.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
import tendencias as t  # noqa: E402


def stats(n_years=24, lag1=0.0):
    return {"n_years": n_years, "lag1": lag1, "p_value": 0.01}


class Clasificar(unittest.TestCase):
    def test_semaforo(self):
        self.assertEqual(t.clasificar(stats(), 0.049, 4)["status"], "real")
        self.assertEqual(t.clasificar(stats(), 0.05, 4)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(n_years=19), 0.001, 4)["status"], "pocos_datos")
        self.assertEqual(t.clasificar(stats(), 0.001, 3)["status"], "pocos_datos")

    def test_status_coincide_con_q_publicado(self):
        st = t.clasificar(stats(), 0.0499996, 10)  # se publica 0.05
        self.assertEqual(st["q_value"], 0.05)
        self.assertEqual(st["status"], "posible_casualidad")

    def test_aviso(self):
        self.assertNotIn("aviso", t.clasificar(stats(), 0.5, 10))
        imerg = t.VARIABLES["lluvia"]["aviso"]
        self.assertIn("2014", t.clasificar(stats(), 0.5, 10, imerg)["aviso"])
        ambos = t.clasificar(stats(lag1=0.6), 0.5, 10, imerg)["aviso"]
        self.assertTrue(ambos.startswith(imerg) and ambos.endswith(t.AVISO_LAG1))


class Estadisticas(unittest.TestCase):
    def test_recta_exacta(self):
        anios = np.arange(2001, 2025)
        y = 3.0 + 0.02 * anios  # 0,2 por década
        st = t.estadisticas(anios, y, porcentaje=True)
        self.assertAlmostEqual(st["slope_per_decade"], 0.2, places=6)
        recta = st["intercept"] + st["slope_per_decade"] / 10 * anios
        self.assertLess(np.abs(recta - y).max(), 1e-4)
        self.assertEqual((st["year_start"], st["year_end"], st["n_years"]), (2001, 2024, 24))
        self.assertIn("pct_change_per_decade", st)

    def test_lag1_usa_los_anios_reales(self):
        anios = np.array([2001, 2002, 2003, 2010, 2011, 2012])
        y = 0.5 * anios  # recta pura: sin la tendencia no queda nada
        self.assertEqual(t.lag1(anios, y, 0.5), 0.0)


class Periodo(unittest.TestCase):
    def test_solo_2001_2024(self):
        fila = {"region": "Lima", "lat": 0, "lon": 0, "celdas": 9,
                "anios": {str(a): {"T2M": 20.0} for a in range(1981, 2026)}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.json").write_text(json.dumps([fila]))
            antes, t.DATA = t.DATA, Path(tmp)
            try:
                [(_, anios, _)] = t.zonas_de({"archivo": "x.json", "campo": "T2M"})
            finally:
                t.DATA = antes
        self.assertEqual((anios[0], anios[-1], len(anios)), (2001, 2024, 24))


if __name__ == "__main__":
    unittest.main()
