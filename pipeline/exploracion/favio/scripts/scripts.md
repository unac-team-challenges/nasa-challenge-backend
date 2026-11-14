# Scripts de Favio

Todos se corren desde `pipeline/exploracion/favio/` con el entorno de `requirements.txt`:

```bash
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

| Script | Qué hace | Cómo se corre | Sale en |
|---|---|---|---|
| `lab0_login.py` | Inicia sesión en Earthdata y la guarda en el netrc del usuario (fuera del repo) | `python scripts/lab0_login.py` (pide usuario y clave en la terminal) | — |
| `lab1_power.py` | Lab 1: variables, unidades, `-999`, humedad y gráfico del Caso 1 (Piura, Tumbes, Puno, 1981–2024) | `python scripts/lab1_power.py` | `scripts/salida/` |
| `lab3_appeears.py` | Lab 3: pide a AppEEARS el NDVI mensual (MOD13A3) de 6 zonas, 2001–2024, consulta el estado y descarga | `python scripts/lab3_appeears.py enviar`, luego `estado` y `bajar` | `scripts/data/ndvi/` |
| `lab3_analisis.py` | Lab 3: NDVI anual por zona, tendencia (lab5 de Josue), área verde 2001 frente a 2024, meses perdidos por nubes e imágenes del antes y después | `python scripts/lab3_analisis.py` (después de `lab3_appeears.py bajar`) | `scripts/salida/` (copiar a `resultados/` para subirlo) |
| `vista_rapida_fetch.py` | Baja POWER mensual (8 variables) de las 25 capitales, 2000–2024 | `python scripts/vista_rapida_fetch.py <carpeta>` | JSON por departamento |
| `vista_rapida_tendencias.py` | Mann-Kendall, Sen por década, lag1 y BH por variable (sin librerías externas) | `python scripts/vista_rapida_tendencias.py <carpeta>` | consola + `trends_power.json` |
| `vista_rapida_1981_vs_2000.py` | Compara las tendencias de 1981–2024 y 2000–2024 con los mismos datos | `python scripts/vista_rapida_1981_vs_2000.py <carpeta con datos desde 1981>` | consola + `resultados/vista_rapida_1981_vs_2000.json` |

Notas:
- Para el periodo largo, cambiar `start=2000` por `start=1981` en `vista_rapida_fetch.py`.
- La vista rápida usa **un punto por capital**. Para el pipeline vale el método de `josue/scripts/power_departamentos.py`, que promedia todas las celdas del departamento.
- Ningún script guarda credenciales. `lab3_appeears.py` las lee del netrc que crea `lab0_login.py`.
