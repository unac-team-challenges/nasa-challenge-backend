# Conclusiones y propuestas (Favio)

Complementa `../josue/conclusiones.md`, sin repetirlo. Aquí van los hallazgos de mis labs y lo que significan para **el producto y la demo**.

## Lo que encontré con datos reales

1. **El Niño: un contraste listo para el Caso 1** (POWER, lluvia anual):

   | Año | Piura | Tumbes | Puno |
   |---|---|---|---|
   | 1983 (El Niño) | 386 mm | **1080 mm** | **151 mm** |
   | 1998 (El Niño) | **1367** | **2247** | 288 |
   | 2017 (Niño costero) | 670 | 1036 | 496 |
   | Promedio 1981–2024 | 202 | 419 | 421 |

   Los mismos años que inundan el norte secan el altiplano. Sirve como frase del expediente y como escena del video: "la misma causa, efectos opuestos".
   - POWER da para Puno unos 420 mm al año, menos que lo esperado (celda gruesa). **En la ficha, la cifra tiene que salir de IMERG.**

2. **Temperatura:** 21 de 25 capitales con cambio real desde 1981 y 18 desde 2000 (Mann-Kendall + BH, umbral simple). Desde 2000 el ritmo casi se duplica: Apurímac pasa de +0,14 a +0,54 °C/década. El umbral exigente de Josue da 22 de 22. Las dos pruebas apuntan a lo mismo.

3. **Lluvia: el periodo cambia el resultado** (porcentaje por década):

   | Departamento | 1981–2024 | 2000–2024 |
   |---|---|---|
   | Ica | +28 % (real) | +61 % (real) |
   | Lambayeque | +14 % | +43 % (real) |
   | Amazonas | −11 % (real) | −13 % |
   | Apurímac | +5 % | **−21 % (real)** |
   | Loreto | **+12 % (real)** | −7 % |
   | Piura | −13 % | +2 % |

   Ica, Lambayeque y La Libertad suben en los dos periodos; Amazonas baja en los dos. En Apurímac, Loreto y Piura el signo se invierte.

4. **Humedad del suelo de POWER:** los valores vienen con 2 decimales (por ejemplo 0,38), así que Sen da 0 en muchos departamentos. No es confiable para tendencias.

5. **Mi cuenta de Earthdata funciona** con `earthaccess.login(persist=True)` y con la API de AppEEARS (token por `/login`, credenciales leídas del netrc local, nunca en el código).

## Propuestas para el producto (las decide el equipo)

| # | Propuesta | Por qué |
|---|---|---|
| 1 | La ficha muestra siempre el **periodo** ("2001–2024, IMERG") | La lluvia cambia de signo según el periodo |
| 2 | **Pista "desde 1981 / desde 2001"** en las zonas donde el signo se invierte | Convierte la limitación en algo que el usuario aprende |
| 3 | Escena de **El Niño 1983 y 1998** en el Expediente 1 (norte inundado, altiplano seco) | Es el gancho del reto con datos de NASA |
| 4 | Lluvia en **porcentaje por década** en la ficha; mm solo en el detalle | 40 mm en Ica y en Loreto no significan lo mismo |
| 5 | **No** agregar humedad del suelo de POWER como cuarta variable | Viene redondeada |
| 6 | Años completos **2001–2024** para IMERG y MODIS | Evita un año a medias en la tendencia |
| 7 | Usar mi cuenta de Earthdata para el **Lab 2 (IMERG y GPCP)** mientras se desbloquea la de Josue | Hoy es la única que funciona |

## Lo que falta

- [x] **Lab 3 terminado** (MODIS MOD13A3, 2001–2024):
  - **Chavimochic:** área verde de 189 a 355 km², NDVI de 0,19 a 0,31; Sen +0,054 por década, p < 0,0001.
  - **Ica-Villacurí:** de 118 a 222 km², NDVI de 0,14 a 0,20; Sen +0,027 por década, p < 0,0001.
  - **Olmos:** sin tendencia (p = 0,43). El recuadro cayó sobre bosque seco natural y no sobre las tierras nuevas del proyecto: hay que moverlo.
  - **Selva:** saturada (NDVI ~0,85 fijo); el NDVI no sirve ahí. **Lima** pierde 13 de 288 meses por la garúa; la selva, 8; la sierra, ninguno.
  - Las imágenes de `resultados/lab3_antes_despues.png` sirven para el antes y después del Caso 2 (`react-compare-slider`).
- [ ] Mover el recuadro de Olmos a las tierras irrigadas del proyecto y volver a pedirlo.
- [ ] Coordinar con Josue quién corre el Lab 2 con una cuenta que funcione.
