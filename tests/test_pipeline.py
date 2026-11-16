"""Pruebas de los avisos y del modo incremental del pipeline (sin red)."""
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import gpm  # noqa: E402
import ndvi  # noqa: E402
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


class VersionesNuevas(unittest.TestCase):
    def _buscar(self, *versiones, **kw):
        cols = [SimpleNamespace(version=v) for v in versiones]
        with mock.patch.object(gpm.earthaccess, "search_datasets", return_value=cols, **kw):
            return gpm.versiones_nuevas()

    def test_solo_v07_no_avisa(self):
        self.assertEqual(self._buscar("07"), [])

    def test_aparece_v08(self):
        self.assertEqual(self._buscar("07", "08"), ["08"])

    def test_sin_red_avisa_y_sigue(self):
        err = io.StringIO()
        with mock.patch.object(gpm.earthaccess, "search_datasets", side_effect=OSError("sin red")), \
                mock.patch.object(sys, "stderr", err):
            self.assertEqual(gpm.versiones_nuevas(), [])
        self.assertIn("AVISO", err.getvalue())


class Avisos(unittest.TestCase):
    def test_power_avisa_anios_descartados(self):
        salida = io.StringIO()
        power.avisar_incompletos({2026: list(power.REGIONES), 2003: ["Callao"]}, salida)
        lineas = salida.getvalue().splitlines()
        self.assertEqual(lineas, ["AVISO 2003: sin 12 meses en Callao; ese año no entra",
                                  "AVISO 2026: sin 12 meses en 25 regiones; ese año no entra"])


class LeerNetcdf(unittest.TestCase):
    """_leer_zona con un NetCDF sintético como los de AppEEARS (revisión de #42, Leandro)."""

    def test_fechas_datetime64(self):
        import tempfile

        import numpy as np
        import pandas as pd
        import xarray as xr

        o, s, e, n = ndvi.ZONAS[0][5]
        tiempo = pd.date_range("2001-01-01", periods=24, freq="MS")  # se decodifica como datetime64
        lat, lon = np.linspace(s + 0.01, n - 0.01, 3), np.linspace(o + 0.01, e - 0.01, 3)
        forma = (len(tiempo), len(lat), len(lon))
        ds = xr.Dataset(
            {ndvi.CAPAS[0]: (("time", "lat", "lon"), np.full(forma, 0.4)),
             ndvi.CAPAS[1]: (("time", "lat", "lon"), np.zeros(forma))},
            coords={"time": tiempo, "lat": lat, "lon": lon})
        with tempfile.TemporaryDirectory() as tmp:
            ds.to_netcdf(Path(tmp) / "zona.nc", engine="h5netcdf")
            antes, ndvi.CACHE = ndvi.CACHE, Path(tmp)
            try:
                pixeles, meses, areas = ndvi._leer_zona(ndvi.ZONAS[0])
            finally:
                ndvi.CACHE = antes
        self.assertEqual(pixeles, 9)
        self.assertEqual(meses[0][:3], (2001, 1, True))
        self.assertEqual(meses[-1][:2], (2002, 12))
        self.assertEqual(sorted(areas), [2001, 2002])


if __name__ == "__main__":
    unittest.main()
