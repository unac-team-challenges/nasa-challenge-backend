# Conclusiones y cambios propuestos al plan

## Lo que ya se puede afirmar (con datos reales)

1. **La temperatura sube en todo el Perú analizable.** Con POWER (MERRA-2), en 1981–2024, los 22 departamentos analizables tienen tendencia `real` con el umbral exigente: entre +0,13 y +0,45 °C por década, mediana +0,21. Desde 2001 el ritmo es mayor (+0,30) pero menos seguro (11 de 22). **Es el hallazgo más sólido para la demo.**
2. **La lluvia cambia de signo según la región y el periodo.** Baja en Ucayali, Piura y Amazonas; sube en Ica, Arequipa, Ayacucho y Apurímac (1981–2024). En Apurímac, Loreto y Piura el signo depende del periodo. Es exactamente lo que plantea el reto, pero con POWER solo vale como **tercera opinión**: la ficha tiene que salir de IMERG y GPCP.
3. **El método funciona y está validado** contra `pymannkendall`, `scipy` y `statsmodels` (192 series, diferencias en p < 1e-15).
4. **El umbral exigente filtra lo que tiene que filtrar:** el artefacto de lluvia en Iquitos y Loreto (`lag1` alto), la lluvia de Lima (autocorrelación) y las series de 24 años sin potencia.

## Cambios propuestos (avisar a los 4 antes de tocar el contrato)

| # | Cambio | Motivo | Dónde |
|---|---|---|---|
| 1 | Periodo largo de lluvia: **1983–2023** | GPCP v3.2 termina en 2023-12 (CMR) | Documento 13, sección 3 |
| 2 | IMERG: **termina en 2025-09** y en CMR empieza en **1998-01** | CMR: 333 archivos mensuales | Documentos 02, 06 y 13 |
| 3 | IMERG en **mm/hr** → ×24 para mm/día | Registro de la variable en CMR | Pipeline |
| 4 | **Umbral exigente** (`real` = q < 0,05 + IC sin 0 + \|lag1\| ≤ 0,5; `pocos_datos` = menos de 4 celdas o menos de 20 años) | Evita falsos `real` | Pipeline + textos de la ficha |
| 5 | Campo nuevo **`motivo`** junto a `status` | Explicar por qué no es `real` | Contrato (opcional) |
| 6 | Campo **`celdas`** en `stats` | Justificar `pocos_datos` | Contrato (opcional) |
| 7 | **Callao: sin dato** en POWER y GPCP; con IMERG, 1 celda | Lab 4 | Ficha y mapa |
| 8 | Promediar **todas las celdas** del departamento, no un punto por capital | Loreto tiene 97 celdas de POWER | Pipeline |
| 9 | POWER regional en **4 recuadros** (máximo 10° por lado) | Error de la API | Pipeline |
| 10 | Usar las librerías en el pipeline (no la implementación propia) | Ya son equivalentes; menos código | Pipeline |

## Lo que falta

- [ ] **Desbloquear la cuenta de Earthdata** (Josue) → Lab 2 (IMERG y GPCP) y Lab 3 (AppEEARS).
- [ ] Repetir `power_departamentos.py` con IMERG y GPCP: el mismo flujo, cambiando la fuente.
- [ ] Comparar la lluvia de Ucayali, Piura e Ica entre POWER, IMERG y GPCP.
- [ ] Confirmar la lista oficial de recursos del reto (spaceappschallenge.org).
