#!/usr/bin/env python3
"""
Generador de Fig. 1: Caracterizacion termica experimental del servomotor MG90S.
Guarda la figura en formato vectorial PDF y PNG de alta resolucion (300 DPI)
con tipografia estandar IEEE (Times-like/Computer Modern) y etiquetas matematicas limpias.
"""

import os
import openpyxl
import numpy as np
import matplotlib.pyplot as plt

# Configuracion de estilo IEEE Transactions
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.labelsize': 9,
    'legend.fontsize': 8,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.autolayout': True,
    'mathtext.fontset': 'stix',
})

EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../docs/experimental-data/servomotor_pruebas_caracterizacion.xlsx"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../figures"))

wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

# 1. Datos Trial 1 (ROTO 1)
s1 = wb['ROTO 1']
t1 = []
temp1 = []
for r in range(2, s1.max_row + 1):
    vt = s1.cell(r, 1).value
    vtemp = s1.cell(r, 3).value
    if vt is not None and vtemp is not None:
        t1.append(float(vt))
        temp1.append(float(vtemp))

t1 = np.array(t1)
temp1 = np.array(temp1)
t1 = t1 - t1[0]  # Normalizar inicio a 0 s

# 2. Datos Trial 2 (Hoja2)
s2 = wb['Hoja2']
t2 = []
temp2 = []
for r in range(2, s2.max_row + 1):
    vt = s2.cell(r, 1).value
    vtemp = s2.cell(r, 3).value
    if vt is not None and vtemp is not None:
        t2.append(float(vt))
        temp2.append(float(vtemp))

t2 = np.array(t2)
temp2 = np.array(temp2)
t2 = t2 - t2[0]  # Normalizar inicio a 0 s

# Crear figura de 2 paneles (formato ancho de columna IEEE: 3.5 in)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.6), dpi=300)

# --- Subplot (a): Trial 1 ---
ax1.plot(t1, temp1, color='#d9534f', linewidth=1.5, label=r'Measured $T_s(t)$')
ax1.scatter([t1[-1]], [temp1[-1]], color='#900C3F', s=35, zorder=5, label=r'Peak $T_{\max} = 64.84\,^\circ\mathrm{C}$')
ax1.axhline(temp1[0], color='gray', linestyle=':', linewidth=1.0, label=r'Ambient $T_a = 21.37\,^\circ\mathrm{C}$')
ax1.set_title(r'(a) Trial 1: Heating under continuous stall', fontsize=8.5)
ax1.set_xlabel(r'Time $t$ ($\mathrm{s}$)')
ax1.set_ylabel(r'Temperature ($^\circ\mathrm{C}$)')
ax1.set_xlim([0, 235])
ax1.set_ylim([18, 70])
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='lower right', framealpha=0.9)

# --- Subplot (b): Trial 2 ---
ax2.plot(t2, temp2, color='#0275d8', linewidth=1.4, label=r'Measured $T_s(t)$')
idx_peak = np.argmax(temp2)
ax2.scatter([t2[idx_peak]], [temp2[idx_peak]], color='#003366', s=35, zorder=5, label=r'Peak $T_{\max} = 70.21\,^\circ\mathrm{C}$')
ax2.axhline(temp2[0], color='gray', linestyle=':', linewidth=1.0, label=r'Ambient $T_a = 19.29\,^\circ\mathrm{C}$')
ax2.set_title(r'(b) Trial 2: Extended thermal cycle', fontsize=8.5)
ax2.set_xlabel(r'Time $t$ ($\mathrm{s}$)')
ax2.set_ylabel(r'Temperature ($^\circ\mathrm{C}$)')
ax2.set_xlim([0, 700])
ax2.set_ylim([18, 75])
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='lower right', framealpha=0.9)

plt.tight_layout()

# Guardar figura en figures/
png_out = os.path.join(OUTPUT_DIR, "fig_thermal_response.png")
pdf_out = os.path.join(OUTPUT_DIR, "fig_thermal_response.pdf")
fig.savefig(png_out, dpi=300)
fig.savefig(pdf_out)
print(f"Figuras guardadas exitosamente en:\n  {png_out}\n  {pdf_out}")
