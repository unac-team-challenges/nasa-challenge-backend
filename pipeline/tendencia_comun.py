"""Criterio único para decir «tendencia real» (docs/tendencias.md §2b).

Lo usan pipeline/tendencias.py y pipeline/ndvi.py. Es el único lugar del pipeline
donde se decide: no copiar los umbrales en otro archivo.

real = q < 0.05  y  el IC95 de Sen no incluye 0  y  |lag1| <= 0.5
El p-valor (TFPW, serie pre-blanqueada) y el IC (Sen, serie original) son pruebas
distintas y pueden discrepar: exigir las dos evita mostrar «real» con un IC que cruza 0.
"""
ALFA, MAX_LAG1 = 0.05, 0.5

AVISO_IC = ("El intervalo de la tendencia incluye 0: aunque la prueba sale significativa, "
            "no se puede asegurar si sube o baja.")
AVISO_LAG1 = "Años muy parecidos entre sí (lag1 alto): la tendencia puede parecer más segura de lo que es"


def evaluar(q, ci_low, ci_high, lag1):
    """Devuelve (es_real, avisos). Los avisos explican en lenguaje simple por qué una
    tendencia significativa no se marca real, o que la autocorrelación es alta."""
    ic_cruza_cero = ci_low <= 0 <= ci_high
    lag1_alto = abs(lag1) > MAX_LAG1
    avisos = []
    if q < ALFA and ic_cruza_cero:
        avisos.append(AVISO_IC)
    if lag1_alto:
        avisos.append(AVISO_LAG1)
    return q < ALFA and not ic_cruza_cero and not lag1_alto, avisos
