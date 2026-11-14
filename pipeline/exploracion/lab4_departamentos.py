"""Laboratorio 4 (guía 12): cuántas celdas de cada dataset caen en cada departamento.

Solo usa la forma de la grilla (centros de celda), no descarga datos.
- POWER: grilla nativa de MERRA-2, 0.5° lat x 0.625° lon.
- IMERG: 0.1° x 0.1°, centros en x.x5.
"""
import os

import geopandas as gpd
import numpy as np
import regionmask

ARCHIVO = "data/geojson/peru_departamentos.geojson"
gdf = gpd.read_file(ARCHIVO)
print(f"GeoJSON: {len(gdf)} departamentos, {os.path.getsize(ARCHIVO)/1024:.0f} KB, "
      f"columnas={gdf.columns.tolist()}, ubigeo tipo={type(gdf['FIRST_IDDP'][0]).__name__}")

regiones = regionmask.from_geopandas(gdf, names="NOMBDEP", numbers=None)


def contar(lats, lons):
    mascara = regiones.mask(lons, lats)
    return {i: int((mascara == i).sum()) for i in range(len(gdf))}


oeste, sur, este, norte = -81.5, -18.5, -68.5, 0.1
# POWER / MERRA-2: centros en múltiplos de 0.5 (lat) y 0.625 (lon)
power_lat = np.arange(np.ceil(sur / 0.5) * 0.5, norte, 0.5)
power_lon = np.arange(np.ceil(oeste / 0.625) * 0.625, este, 0.625)
# IMERG: centros en x.x5
imerg_lat = np.round(np.arange(-18.45, 0.1, 0.1), 2)
imerg_lon = np.round(np.arange(-81.45, -68.5, 0.1), 2)

power = contar(power_lat, power_lon)
imerg = contar(imerg_lat, imerg_lon)

filas = sorted(range(len(gdf)), key=lambda i: imerg[i])
print(f"\n{'ubigeo':6} {'departamento':15} {'POWER':>6} {'IMERG':>6}")
for i in filas:
    print(f"{gdf['FIRST_IDDP'][i]:6} {gdf['NOMBDEP'][i]:15} {power[i]:6} {imerg[i]:6}")

sin_power = [gdf["NOMBDEP"][i] for i in range(len(gdf)) if power[i] == 0]
print("\nSin ninguna celda de POWER:", sin_power or "ninguno")
