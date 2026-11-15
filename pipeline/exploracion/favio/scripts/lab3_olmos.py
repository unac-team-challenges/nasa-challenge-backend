"""Laboratorio 3b: NDVI de Olmos con el recuadro movido a las tierras nuevas (MOD13A3 vía AppEEARS).

Historia (para que quede claro el orden): el recuadro del Lab 3 (-80.00, -6.10, -79.75, -5.85) dio
p = 0,43 y se descartó DESPUÉS de ver ese resultado, porque caía sobre bosque seco cerca del pueblo
de Olmos. El recuadro nuevo se eligió con un dato independiente del NDVI, antes de ver su propio
NDVI: la caja de 0,25° con más campos de cultivo en OpenStreetMap (landuse=farmland/orchard;
~4.400 polígonos, frente a ~150 en la caja vieja; Overpass, 2026-11-15). La prueba descartada se
cuenta en Benjamini-Hochberg (PRUEBAS_DESCARTADAS en pipeline/ndvi.py) y Olmos lleva un aviso.

Reutiliza pipeline/ndvi.py (misma solicitud, mismas capas) con solo la zona de Olmos, tomada de
ndvi.ZONAS. Hoy `python pipeline/ndvi.py enviar` ya pide las 3 zonas juntas: este script solo
reproduce la solicitud suelta que se hizo (tarea ee736bc9).

Uso (desde esta carpeta):
  python lab3_olmos.py enviar   -> crea la solicitud y guarda el task_id en data/lab3_olmos_task.json
  python lab3_olmos.py estado   -> consulta el estado (~3 h)
  python lab3_olmos.py bajar    -> descarga el NetCDF a data/ndvi_olmos/
Credenciales: las de pipeline/ndvi.py (nunca se imprimen). data/ está en .gitignore.
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2]))  # pipeline/

import ndvi  # noqa: E402

TASK = AQUI / "data" / "lab3_olmos_task.json"
SALIDA = AQUI / "data" / "ndvi_olmos"
OLMOS = [z for z in ndvi.ZONAS if z[0] == "olmos"]


if __name__ == "__main__":
    acciones = {
        "enviar": lambda: ndvi.enviar(OLMOS, TASK, "detective-peru-lab3-olmos"),
        "estado": lambda: ndvi.consultar(TASK),
        "bajar": lambda: ndvi.bajar(TASK, SALIDA),
    }
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        sys.exit(f"uso: python lab3_olmos.py {{{'|'.join(acciones)}}}")
    acciones[sys.argv[1]]()
