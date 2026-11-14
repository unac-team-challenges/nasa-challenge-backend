# Registro de pruebas de: Josue
Fecha y hora: sábado 14 de noviembre de 2026, tarde (Lima)

| Dataset | ¿Funcionó? | Tiempo | Peso del archivo | Unidades | Problemas o errores |
|---|---|---|---|---|---|
| NASA POWER | ✅ Puntos y malla regional, 1981–2024 | ~1 s por punto; ~2 s por recuadro | 58 KB por punto; 1,1–2,3 MB por recuadro y variable | °C, mm/día, %, g/kg, 0–1 | Regional: máximo 10° por lado. Artefacto de lluvia en Iquitos y Loreto |
| IMERG | ⛔ Bloqueado (credencial) | — | 16,6–18,3 MB/mes (CMR) | mm/hr (CMR) | Termina en 2025-09; en CMR empieza en 1998-01 |
| GPCP v3.2 | ⛔ Bloqueado (credencial) | — | ~6,5 MB/mes (CMR) | mm/day (CMR) | Termina en 2023-12 |
| MODIS MOD13A3 | Solo metadatos (Bruno) | 0,5 s | — | NDVI × 0,0001; relleno -3000 | El login de AppEEARS falla (credencial) |
| GeoJSON | ✅ | <1 s | 140 KB | — | Ninguno: el ubigeo ya es texto |

## Qué encontré
- **Nombres que funcionaron:** POWER `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `GWETTOP`, `RH2M`, `QV2M`. IMERG `Grid/precipitation`. GPCP `sat_gauge_precip`. AppEEARS `_1_km_monthly_NDVI`. GeoJSON `FIRST_IDDP` y `NOMBDEP`.
- **Lo que NO funcionó:** login de Earthdata (`invalid_credentials`); el CLI de Bruno (npm sin acceso); la consulta regional de POWER con más de 10°.
- **Unidades:** las de la tabla. IMERG × 24 = mm/día.
- **Departamentos con pocas celdas:** Callao (IMERG 1, GPCP 0, POWER 0), Tumbes (GPCP 2, POWER 1), Lambayeque (POWER 3).
- **Cosas raras:** lluvia de POWER en Iquitos 2003–2006 (artefacto, `lag1` 0,74); lluvia de Lima "significativa" pero de +0,03 mm/día por década; POWER devuelve la elevación media de la celda.

## Respuestas a las preguntas de mi laboratorio
Ver `labs/`: [lab1-power.md](labs/lab1-power.md), [lab2-imerg-gpcp.md](labs/lab2-imerg-gpcp.md), [lab4-celdas-departamento.md](labs/lab4-celdas-departamento.md), [lab5-tendencias.md](labs/lab5-tendencias.md) y, además, [power-departamentos.md](labs/power-departamentos.md).

## Lo que cambiaría en el plan
Ver [conclusiones.md](conclusiones.md) (10 cambios). Los principales: lluvia larga 1983–2023, umbral exigente, Callao sin dato y promediar todas las celdas.

## Nota de seguridad
La contraseña de la cuenta **secundaria** de Earthdata de Josue se compartió en una sesión con un asistente de IA (14 nov 2026). **Decisión del dueño:** cuenta secundaria creada para el reto, no se rota. La contraseña no está en ningún archivo del proyecto ni del Drive; solo en `~/.netrc` (permiso 600) de la laptop. Ver [proceso-y-entorno.md](proceso-y-entorno.md).
