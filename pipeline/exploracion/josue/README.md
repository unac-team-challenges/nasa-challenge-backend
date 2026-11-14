# Labs de Josue — validación de datasets y primeras tendencias reales (Perú)

**Equipo:** NASA-CHALLENGE-UNAC · **Rol:** datos (pipeline Python) · **Fecha:** sábado 14 nov 2026
**Cubre:** `12-guia-probar-datasets-peru.md` (labs 0, 1, 2, 4 y 5), `13-datos-unificado-14nov.md` y la sección "Datos" de `stack-decidido.md`.

## Resumen en 6 líneas

1. **Temperatura (POWER, 1981–2024): sube en los 22 departamentos analizables**, con tendencia `real` en todos: entre +0,13 y +0,45 °C por década (mediana +0,21). Con el umbral exigente es la señal más sólida del proyecto.
2. **Lluvia (POWER, tercera opinión): 7 de 22 departamentos tienen tendencia `real` y el signo cambia según la región** (baja en Ucayali, Piura y Amazonas; sube en Ica, Arequipa, Ayacucho y Apurímac). Es justo el caso del reto: el mismo dato sube en una región y baja en otra.
3. **El método está validado:** la implementación propia coincide con `pymannkendall`, `scipy` y `statsmodels` en 192 series (diferencia en p < 1e-15).
4. **Callao no se puede analizar** con POWER ni con GPCP (0 celdas). Tumbes y Lambayeque quedan como `pocos_datos` con POWER.
5. **Correcciones al plan:** GPCP v3.2 termina en 2023-12 e IMERG en 2025-09 (verificado en CMR).
6. **Bloqueado:** IMERG y GPCP (Lab 2) y AppEEARS. La cuenta de Earthdata responde `Invalid user credentials`.

## Estado

| Módulo | Qué | Estado |
|---|---|---|
| [labs/lab1-power.md](labs/lab1-power.md) | NASA POWER, 5 puntos | ✅ |
| [labs/lab2-imerg-gpcp.md](labs/lab2-imerg-gpcp.md) | IMERG + GPCP con `earthaccess` | ⛔ Bloqueado por la credencial (script listo, metadatos verificados) |
| [labs/lab4-celdas-departamento.md](labs/lab4-celdas-departamento.md) | GeoJSON + celdas por departamento | ✅ Validado con `regionmask` |
| [labs/lab5-tendencias.md](labs/lab5-tendencias.md) | Método de tendencia + validación | ✅ Validado contra las librerías |
| [labs/power-departamentos.md](labs/power-departamentos.md) | **Tendencias reales por departamento** (POWER) | ✅ |
| [bruno/bruno.md](bruno/bruno.md) | Colección de Bruno y cómo usarla | ✅ |
| [bruno/resultados-bruno.md](bruno/resultados-bruno.md) | Resultados de ejecutar la colección | ✅ 10 de 12 peticiones (2 necesitan credencial) |
| [scripts/scripts.md](scripts/scripts.md) | Qué hace cada script y en qué orden se corre | ✅ |
| [proceso-y-entorno.md](proceso-y-entorno.md) | Entorno, reproducibilidad, seguridad | ✅ |
| [conclusiones.md](conclusiones.md) | Hallazgos y cambios propuestos al plan | ✅ |
| [registro-Josue.md](registro-Josue.md) | Registro con la plantilla del equipo | ✅ |

## Estructura

```
pipeline/exploracion/josue/
  README.md  conclusiones.md  proceso-y-entorno.md  registro-Josue.md
  labs/        un .md por laboratorio
  bruno/       bruno.md, resultados-bruno.md, coleccion/ (los .yml de Bruno)
  scripts/     scripts.md + los 8 scripts .py
  resultados/  PNG, CSV y JSON pequeños
```
