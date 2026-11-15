"""Pruebas de pipeline/tendencias.py. Uso: python -m unittest tests/test_tendencias.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
import tendencias as t  # noqa: E402


def stats(n_years=24, lag1=0.0, ci=(0.1, 0.3)):
    return {"n_years": n_years, "lag1": lag1, "p_value": 0.01, "ci_low": ci[0], "ci_high": ci[1]}


class Clasificar(unittest.TestCase):
    def test_semaforo(self):
        self.assertEqual(t.clasificar(stats(), 0.049, 4)["status"], "real")
        self.assertEqual(t.clasificar(stats(), 0.05, 4)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(n_years=19), 0.001, 4)["status"], "pocos_datos")
        self.assertEqual(t.clasificar(stats(), 0.001, 3)["status"], "pocos_datos")

    def test_criterio_unico(self):
        # q < 0.05 no basta: el IC no puede cruzar 0 (caso Loreto) ni |lag1| pasar de 0.5 (caso Huánuco)
        self.assertEqual(t.clasificar(stats(ci=(-0.0046, 0.5535)), 0.044, 9)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(ci=(-0.3, -0.1)), 0.01, 9)["status"], "real")
        self.assertEqual(t.clasificar(stats(lag1=0.54), 0.013, 9)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(lag1=-0.6), 0.013, 9)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(lag1=0.5), 0.013, 9)["status"], "real")

    def test_imerg_nunca_sale_real_y_power_si_puede(self):
        # Opción C (2026-11-15): la lluvia principal es POWER; IMERG (lluvia_imerg) es la segunda fuente
        self.assertTrue(t.VARIABLES["lluvia_imerg"]["sin_real"])
        self.assertNotIn("sin_real", t.VARIABLES["lluvia"])
        self.assertNotIn("sin_real", t.VARIABLES["temperatura"])
        self.assertEqual(t.VARIABLES["lluvia"]["archivo"], "power.json")
        self.assertEqual(t.VARIABLES["lluvia_imerg"]["archivo"], "gpm.json")
        self.assertEqual(t.clasificar(stats(), 0.001, 4, sin_real=True)["status"], "posible_casualidad")
        self.assertEqual(t.clasificar(stats(n_years=19), 0.001, 4, sin_real=True)["status"], "pocos_datos")

    def test_status_coincide_con_q_publicado(self):
        st = t.clasificar(stats(), 0.0499996, 10)  # se publica 0.05
        self.assertEqual(st["q_value"], 0.05)
        self.assertEqual(st["status"], "posible_casualidad")

    def test_aviso(self):
        self.assertNotIn("aviso", t.clasificar(stats(), 0.5, 10))
        imerg = t.VARIABLES["lluvia_imerg"]["aviso"]
        self.assertIn("2014", t.clasificar(stats(), 0.5, 10, imerg)["aviso"])
        ambos = t.clasificar(stats(lag1=0.6), 0.5, 10, imerg)["aviso"]
        self.assertTrue(ambos.startswith(imerg) and ambos.endswith(t.AVISO_LAG1))

    def test_aviso_de_ucayali_sale_de_la_serie(self):
        anios = np.arange(2001, 2025)
        y = np.concatenate([np.full(22, 25.0) + 0.01 * np.arange(22), [28.2, 28.5]])
        texto = t.aviso_ucayali(anios, y, {"slope_per_decade": 0.77})
        self.assertIn("2023 y 2024", texto)
        self.assertIn("28,2 y 28,5 °C", texto)
        self.assertIn("de 0,77 a 0,", texto)
        # con un año más, el aviso habla de los dos últimos años y no queda viejo
        mas = t.aviso_ucayali(np.arange(2001, 2026), np.append(y, 27.0), {"slope_per_decade": 0.7})
        self.assertIn("2024 y 2025", mas)
        self.assertEqual(list(t.VARIABLES["temperatura"]["avisos_zona"]), ["25"])

    def test_aviso_explica_por_que_no_es_real(self):
        # lag1 negativo: baja el status y también avisa (antes solo avisaba con lag1 > 0.5)
        self.assertIn(t.AVISO_LAG1, t.clasificar(stats(lag1=-0.6), 0.013, 9)["aviso"])
        # significativa pero con IC que cruza 0 (Loreto): el aviso lo dice
        loreto = t.clasificar(stats(ci=(-0.0046, 0.5535)), 0.044, 9)
        self.assertIn("incluye 0", loreto["aviso"])
        # no significativa: que el IC cruce 0 es lo esperable, sin aviso
        self.assertNotIn("aviso", t.clasificar(stats(ci=(-0.1, 0.2)), 0.4, 9))


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
