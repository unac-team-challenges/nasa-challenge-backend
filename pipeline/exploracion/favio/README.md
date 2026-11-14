# Labs de Favio: exploración de datos con mirada de producto (Perú)

**Equipo:** NASA-CHALLENGE-UNAC · **Rol:** producto, UI/UX y narrativa · **Fecha:** sábado 14 nov 2026
**Cubre:** `12-guia-probar-datasets-peru.md` (labs 0, 1 y 3), `13-datos-unificado-14nov.md` y `14-vista-rapida-datos-14nov.md` (Drive).

## Resumen en 7 líneas

1. **Mi cuenta de Earthdata funciona** (Lab 0). Con ella hice el **Lab 3 (MODIS NDVI por AppEEARS)**, y puede servir para desbloquear el Lab 2 (IMERG y GPCP).
2. **La costa que reverdece se confirma con MODIS** (Lab 3): entre 2001 y 2024, el área verde (NDVI > 0,3) de **Chavimochic pasó de 189 a 355 km²** y la de **Ica-Villacurí de 118 a 222 km²** (+88 % en ambos), con tendencia significativa (Sen + TFPW, IC sin 0). El Caso 2 se sostiene con datos reales.
3. **El Niño inunda el norte y seca el altiplano a la vez** (Lab 1, POWER). En 1983, Tumbes recibió 1080 mm y Puno 151; en 1998, Tumbes 2247 y Puno 288. Es el gancho del reto contado con datos: la misma causa da efectos opuestos.
4. **La temperatura sube en casi todo el Perú** (vista rápida de 25 capitales): 21 de 25 con cambio real desde 1981, unos +0,2 °C por década. Desde 2000 el ritmo casi se duplica. Coincide con `josue/`.
5. **La lluvia depende del periodo:** en Apurímac, Loreto y Piura el signo se invierte entre 1981–2024 y 2000–2024. Para el producto, la ficha tiene que decir siempre **desde qué año** se calcula.
6. **La humedad del suelo de POWER (`GWETTOP` y `GWETROOT`) viene redondeada a 2 decimales**, así que muchas pendientes salen en 0. No sirve como cuarta variable.
7. **Usar años completos 2001–2024** para IMERG y MODIS: IMERG empieza a mitad de 2000 y MODIS en febrero de 2000.

## Estado

| Módulo | Qué | Estado |
|---|---|---|
| Lab 0 | Login de Earthdata con `earthaccess` (`scripts/lab0_login.py`) | ✅ |
| Lab 1 | NASA POWER: unidades, `-999`, humedad, Caso 1 (`scripts/lab1_power.py`) | ✅ |
| Lab 3 | MODIS MOD13A3 (NDVI) por la API de AppEEARS, 6 zonas, 2001–2024 (`scripts/lab3_appeears.py` y `scripts/lab3_analisis.py`) | ✅ AppEEARS tardó ~3 h; análisis y antes/después en `resultados/` |
| Vista rápida | Tendencias de 8 variables de POWER en 25 capitales, 1981–2024 frente a 2000–2024 | ✅ |
| [conclusiones.md](conclusiones.md) | Hallazgos y propuestas para el producto | ✅ |
| [registro-Favio.md](registro-Favio.md) | Registro con la plantilla del equipo | ✅ Labs 0, 1 y 3 |
| [scripts/scripts.md](scripts/scripts.md) | Qué hace cada script y cómo se corre | ✅ |

## Estructura

```
pipeline/exploracion/favio/
  README.md  conclusiones.md  registro-Favio.md  requirements.txt  .gitignore
  scripts/     scripts.md + labs 0, 1 y 3 + 3 scripts de la vista rápida
  resultados/  power_caso1.png, power_caso1_anual.csv, vista_rapida_1981_vs_2000.json,
               lab3_ndvi_anual.png, lab3_antes_despues.png, lab3_resumen.json
```

No toca `src/`, `data/` ni `pipeline/power.py`. Son scripts de exploración, igual que `josue/` y los de Sebastian.
