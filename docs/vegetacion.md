# Vegetación (NDVI): estado y límites

Resultado del Lab 3 de Favio (MODIS MOD13A3, 2001–2024, 6 zonas). Detalle y código en `pipeline/exploracion/favio/`. Reglas que aplican: [`reglas-datos.md`](reglas-datos.md).

## Qué se confirmó
- **Chavimochic:** área verde (NDVI > 0,3) de 189 a 355 km² (+88 %); Sen +0,054 por década, p < 0,0001.
- **Ica-Villacurí:** de 118 a 222 km² (+88 %); Sen +0,027 por década, p < 0,0001.
- Con esto el Caso 2, «la costa que reverdece», se sostiene con datos reales.

## Zonas sin dato útil (decidido el 2026-11-14)
| Zona | Estado | Motivo |
|---|---|---|
| **Olmos** | **Sin dato por ahora. No usar en el producto.** | El recuadro de ~25 × 25 km cayó sobre bosque seco natural, no sobre las tierras irrigadas del proyecto (que empezó en 2014). Sale sin tendencia (p = 0,43) y el área verde baja de 737 a 589 km², lo que **engañaría** si se muestra como «sin reverdecimiento». |
| **Selva (Iquitos)** | No usar NDVI. | Saturado en ~0,85 todo el periodo: no detecta cambios. Si hace falta, otra variable. |
| **Lima** | Usar con cautela. | Pierde 13 de 288 meses por la garúa; área verde mínima (17 → 10 km²). |
| **Valle del Mantaro** | Solo informativo. | El intervalo de la tendencia incluye 0. |

### Para retomar Olmos
1. Mover el recuadro al sur y al oeste, sobre las tierras irrigadas del proyecto.
2. Repetir la solicitud con `scripts/lab3_appeears.py` (AppEEARS tardó ~3 h el 14-nov) y correr `lab3_analisis.py`.
3. Mientras tanto la ficha de Olmos muestra «sin dato», nunca un valor del recuadro actual.

## Pendiente (a cargo de Josue)
La variable de vegetación en `pipeline/` y la revisión de `lab5_tendencias.py` (p-valor frente a IC). Ver la nota del equipo en Drive.
