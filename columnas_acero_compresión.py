# -*- coding: utf-8 -*-
"""
Diseño y revisión de columnas de acero a compresión (IR, CE, ángulos LI/LM, SOL, OS, CS)
AISC 360 / NSR-10 / Eurocódigo  -  Metodología de 6 pasos
Unidades SI: kN, MPa, mm, mm2, mm4, mm6, adimensional

Autora: Anllelina Lopez Romero

Catálogo: Manual de Perfiles Estructurales Gerdau Corsa 2019 (todas las familias de perfiles, págs. 19-35).
K (NSR-10): nomograma de pórticos no arriostrados (AISC 14ª ed., adaptado en NSR-10).

Ejecutar:  streamlit run columnas_acero_compresion.py
Requiere:  streamlit, pandas, numpy, matplotlib
"""
import math

import numpy as np
import pandas as pd
import streamlit as st

AUTORA = "Anllelina Lopez Romero"

st.set_page_config(page_title="Columnas de acero a compresión", page_icon="🏗️", layout="wide")

PI = math.pi
PHI_C = 0.90  # [adimensional] factor de resistencia a compresión

# ----------------------------------------------------------------------------
# Utilidades de formato (LaTeX sin f-strings con llaves)
# ----------------------------------------------------------------------------
U_MPA = r"\,\text{MPa}"
U_KN = r"\,\text{kN}"
U_MM = r"\,\text{mm}"
U_MM2 = r"\,\text{mm}^2"
U_MM4 = r"\,\text{mm}^4"
U_MM6 = r"\,\text{mm}^6"
U_ADIM = r"\ [\text{adim.}]"
NOHAY = r"\text{No hay}"


def n(x, d=2):
    """Número con d decimales."""
    return "{:.{}f}".format(x, d)


def sci(x, d=3):
    """Notación científica en LaTeX."""
    m, e = "{:.{}e}".format(x, d).split("e")
    return m + r"\times 10^{" + str(int(e)) + "}"


def nl(x, d=0):
    """Número o 'No hay' (LaTeX)."""
    return NOHAY if x is None else n(x, d)


# ----------------------------------------------------------------------------
# Catálogo de perfiles IR (Gerdau Corsa 2019). Unidades originales del manual:
# mm (d, tw, bf, tf, T, k, k1, g, g1), cm2 (A), cm4 (I, J), cm3 (S, Z), cm (r), cm6 (Cw)
# Fila: (designación mm x kg/m, in x lb/ft, W/H, d, tw, bf, tf, T, k, k1, g, g1, A, bf/2tf,
#        d/tw, rT, d/Af, Ix, Sx, rx, Iy, Sy, ry, J, Cw, Zx, Zy)
# Valores con erratas evidentes del manual fueron corregidos con relaciones geométricas
# (rx = sqrt(I/A), S = I/c, etc.). Verificar con las tablas oficiales si se usa en proyecto.
# ----------------------------------------------------------------------------
CAT_RAW = [
    ('102x19.4', '4x13', 'H', 106.0, 7.1, 103.0, 8.8, 71.0, 17.0, 11.0, 60.0, 50.0, 24.7, 5.9, 14.9, 2.8, 1.17, 470.0, 89.0, 4.4, 161.0, 31.0, 2.5, 6.2, 3802.76, 103.0, 48.0),
    ('127x23.70', '5x16', 'H', 127.0, 6.1, 127.0, 9.1, 89.0, 19.0, 11.0, 70.0, 50.0, 30.4, 6.9, 20.8, 3.5, 1.1, 887.0, 140.0, 5.4, 313.0, 49.0, 3.2, 7.9, 10877.07, 157.0, 75.0),
    ('127x28.1', '5x19', 'H', 131.0, 6.9, 128.0, 10.9, 90.0, 21.0, 11.0, 70.0, 55.0, 35.7, 5.9, 19.0, 3.5, 0.94, 1091.0, 167.0, 5.5, 380.0, 60.0, 3.3, 12.9, 13702.81, 190.0, 91.0),
    ('152x12.7', '6x8.5', 'W', 148.0, 4.3, 100.0, 4.9, 122.99, 12.54, 9.8, 60.0, 45.0, 16.3, 10.2, 34.3, 2.6, 3.0, 620.0, 84.0, 6.2, 82.0, 17.0, 2.2, 1.4, 4222.3, 93.0, 25.0),
    ('152x13.6', '6x9', 'W', 150.0, 4.3, 100.0, 5.5, 121.0, 14.0, 10.0, 60.0, 45.0, 17.3, 9.1, 34.9, 2.6, 2.74, 683.0, 91.0, 6.3, 91.0, 18.0, 2.3, 1.7, 4750.26, 102.0, 28.0),
    ('152x18.0', '6x12', 'W', 153.0, 5.8, 102.0, 7.1, 121.0, 16.0, 10.0, 60.0, 55.0, 22.9, 7.2, 26.4, 2.7, 2.12, 920.0, 120.0, 6.3, 124.0, 25.0, 2.3, 3.7, 6598.91, 136.0, 38.0),
    ('152x24.0', '6x16', 'W', 160.0, 6.6, 102.0, 10.3, 121.0, 19.0, 11.0, 60.0, 55.0, 30.6, 5.0, 24.2, 2.7, 1.51, 1336.0, 167.0, 6.6, 184.0, 36.0, 2.5, 9.2, 10308.64, 192.0, 56.0),
    ('152x22.4', '6x15', 'H', 152.0, 5.8, 152.0, 6.6, 120.0, 16.0, 10.0, 90.0, 55.0, 28.6, 11.5, 26.2, 4.1, 1.51, 1211.0, 159.0, 6.5, 388.0, 51.0, 3.7, 4.2, 20506.93, 177.0, 78.0),
    ('152x29.7', '6x20', 'H', 157.0, 6.6, 153.0, 9.3, 119.0, 19.0, 11.0, 90.0, 55.0, 37.9, 8.2, 23.8, 4.2, 1.11, 1723.0, 220.0, 6.8, 554.0, 72.0, 3.8, 9.9, 30214.18, 244.0, 110.0),
    ('152x37.2', '6x25', 'H', 162.0, 8.1, 154.0, 11.6, 121.0, 21.0, 11.0, 90.0, 60.0, 47.4, 6.6, 20.0, 4.2, 0.91, 22
