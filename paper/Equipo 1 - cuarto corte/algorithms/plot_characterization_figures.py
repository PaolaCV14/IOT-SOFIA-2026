#!/usr/bin/env python3
"""
Script para generar las figuras de caracterización de corriente (3 paneles a escala 1:1 IEEE)
y la secuencia de simulación cinemática anotada con ejes (X, Y, Z) y objetivo p(t).
"""

import os
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../documents"))
FIG_DIR = os.path.abspath(os.path.join(BASE_DIR, "../figures"))
RESP_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../Equipo 1 - respuesta - tercer corte/figures"))

OUT_DIRS = [FIG_DIR, RESP_DIR]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)


def load_csv_cols(path):
    data = np.genfromtxt(path, delimiter=',', names=True, encoding='utf-8')
    return data['Tiempo_s'], data['Corriente_mA'], data['Temperatura_C']


t5_raw, i5, temp5 = load_csv_cols(os.path.join(DATA_DIR, 'datos_5grados.csv'))
t90_raw, i90, temp90 = load_csv_cols(os.path.join(DATA_DIR, 'datos_901.csv'))
ts_raw, is_mA, temps = load_csv_cols(os.path.join(DATA_DIR, 'datos_CHIDOS_DE_FORZADO.csv'))

t5 = t5_raw - t5_raw[0]
t90 = t90_raw - t90_raw[0]
ts = ts_raw - ts_raw[0]

# Configuración tipográfica IEEE a escala 1:1 (ancho de página IEEE = 7.1 in)
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9.5,
    'axes.labelsize': 9.5,
    'axes.titlesize': 10,
    'legend.fontsize': 8,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'mathtext.fontset': 'stix',
})

# ==============================================================================
# FIGURA: fig_current_characterization (3 paneles de Corriente a tamaño nativo 7.1 in)
# ==============================================================================
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(7.1, 2.35), dpi=300)

# (a) 5 deg
ax1.plot(t5, i5, color='#1f77b4', lw=1.2, label=r'$I(t)$')
ax1.set_title(r'(a) Small Step ($e = 5^\circ$)', fontweight='bold')
ax1.set_xlabel(r'Time $t$ ($\mathrm{s}$)')
ax1.set_ylabel(r'Current ($\mathrm{mA}$)')
ax1.set_xlim([0, 25])
ax1.set_ylim([0, 660])
ax1.axhline(3.1, color='green', linestyle=':', lw=1.1, label=r'Quiesc. $3.1\,\mathrm{mA}$')
max5_idx = int(np.argmax(i5))
ax1.scatter([t5[max5_idx]], [i5[max5_idx]], color='red', s=22, zorder=5)
ax1.annotate(rf'Peak: {i5[max5_idx]:.1f} mA', xy=(t5[max5_idx], i5[max5_idx]),
             xytext=(t5[max5_idx] + 2.2, i5[max5_idx] - 65),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.0),
             fontsize=8, color='red', fontweight='bold')
ax1.legend(loc='upper right', framealpha=0.9)
ax1.grid(True, linestyle='--', alpha=0.5)

# (b) 90 deg
ax2.plot(t90, i90, color='#ff7f0e', lw=1.2, label=r'$I(t)$')
ax2.set_title(r'(b) Large Step ($e = 90^\circ$)', fontweight='bold')
ax2.set_xlabel(r'Time $t$ ($\mathrm{s}$)')
ax2.set_ylabel(r'Current ($\mathrm{mA}$)')
ax2.set_xlim([0, 15])
ax2.set_ylim([0, 660])
ax2.axhline(3.1, color='green', linestyle=':', lw=1.1, label=r'Quiesc. $3.1\,\mathrm{mA}$')
max90_idx = int(np.argmax(i90))
ax2.scatter([t90[max90_idx]], [i90[max90_idx]], color='red', s=22, zorder=5)
ax2.annotate(rf'Peak: {i90[max90_idx]:.1f} mA', xy=(t90[max90_idx], i90[max90_idx]),
             xytext=(1.0, i90[max90_idx] - 75),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.0),
             fontsize=8, color='red', fontweight='bold')
ax2.legend(loc='upper right', framealpha=0.9)
ax2.grid(True, linestyle='--', alpha=0.5)

# (c) Stall
ax3.plot(ts, is_mA, color='#d62728', lw=0.65, alpha=0.85, label=r'$I(t)$')
ax3.set_title(r'(c) Mechanical Stall', fontweight='bold')
ax3.set_xlabel(r'Time $t$ ($\mathrm{s}$)')
ax3.set_ylabel(r'Current ($\mathrm{mA}$)')
ax3.set_xlim([0, 430])
ax3.set_ylim([0, 2000])
ax3.axhline(918.4, color='darkred', linestyle='--', lw=1.2, label=r'Mean: $918.4\,\mathrm{mA}$')
maxs_idx = int(np.argmax(is_mA))
ax3.scatter([ts[maxs_idx]], [is_mA[maxs_idx]], color='darkred', s=22, zorder=5)
ax3.annotate(rf'Surge: {is_mA[maxs_idx]:.0f} mA', xy=(ts[maxs_idx], is_mA[maxs_idx]),
             xytext=(35, is_mA[maxs_idx] - 220),
             arrowprops=dict(arrowstyle='->', color='darkred', lw=1.0),
             fontsize=8, color='darkred', fontweight='bold')
ax3.legend(loc='lower right', framealpha=0.9)
ax3.grid(True, linestyle='--', alpha=0.5)

fig.tight_layout(pad=0.5)
for d in OUT_DIRS:
    fig.savefig(f'{d}/fig_current_characterization.png', dpi=300)
    fig.savefig(f'{d}/fig_current_characterization.pdf')
    # También actualizar fig_characterization_6panels con esta versión legible a escala 1:1
    fig.savefig(f'{d}/fig_characterization_6panels.png', dpi=300)
    fig.savefig(f'{d}/fig_characterization_6panels.pdf')
plt.close(fig)
print("OK: fig_current_characterization generada a escala 1:1 IEEE (7.1 in).")

# ==============================================================================
# FIGURA: Simulación anotada con ejes (X, Y, Z) y objetivo móvil p(t)
# ==============================================================================
fig_sim, axs_sim = plt.subplots(2, 3, figsize=(7.1, 3.8), dpi=300)
target_coords = [
    (0.22, 0.28, r'$\mathbf{p}(t_1)$ (Top-Left)'),
    (0.50, 0.22, r'$\mathbf{p}(t_2)$ (Top-Center)'),
    (0.78, 0.28, r'$\mathbf{p}(t_3)$ (Top-Right)'),
    (0.76, 0.72, r'$\mathbf{p}(t_4)$ (Bottom-Right)'),
    (0.50, 0.78, r'$\mathbf{p}(t_5)$ (Bottom-Center)'),
    (0.24, 0.70, r'$\mathbf{p}(t_6)$ (Bottom-Left)'),
]

for idx, ax in enumerate(axs_sim.flat):
    img_path = os.path.join(FIG_DIR, f'fig_sim_{idx + 1}.png')
    img = mpimg.imread(img_path)
    ax.imshow(img)
    ax.set_xticks([])
    ax.set_yticks([])
    tx, ty, label_p = target_coords[idx]
    h, w = img.shape[0], img.shape[1]
    px, py = tx * w, ty * h

    # Marcar el objetivo p(t)
    ax.scatter([px], [py], color='#ffeb3b', edgecolors='#d32f2f', s=75, linewidths=1.8, zorder=6)
    ax.text(px + 0.04 * w, py, r'$\mathbf{p}(t_' + str(idx + 1) + r')$',
            color='white', fontsize=8.5, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.18', facecolor='#d32f2f', alpha=0.85, edgecolor='none'))

    # Dibujar tríada de ejes de referencia (X, Y, Z) en la esquina inferior izquierda
    ox, oy = 0.11 * w, 0.88 * h
    ax.annotate('', xy=(ox + 0.12 * w, oy), xytext=(ox, oy),
                arrowprops=dict(arrowstyle='->', color='#ff5252', lw=1.4))
    ax.text(ox + 0.13 * w, oy + 0.02 * h, '$X$', color='#ff5252', fontsize=7.5, fontweight='bold')
    ax.annotate('', xy=(ox, oy - 0.14 * h), xytext=(ox, oy),
                arrowprops=dict(arrowstyle='->', color='#69f0ae', lw=1.4))
    ax.text(ox - 0.03 * w, oy - 0.16 * h, '$Y$', color='#69f0ae', fontsize=7.5, fontweight='bold')
    ax.scatter([ox], [oy], color='#40c4ff', s=18, zorder=7)
    ax.text(ox - 0.08 * w, oy + 0.04 * h, '$Z\\odot$', color='#40c4ff', fontsize=7, fontweight='bold')

    ax.set_title(rf'({chr(97 + idx)}) Frame $t_{idx + 1}$: {label_p.split()[-1][1:-1]}', fontsize=8.5, pad=3)

fig_sim.tight_layout(pad=0.35)
for d in OUT_DIRS:
    fig_sim.savefig(f'{d}/fig_simulation_annotated.png', dpi=300)
    fig_sim.savefig(f'{d}/fig_simulation_annotated.pdf')
plt.close(fig_sim)
print("OK: fig_simulation_annotated generada con ejes (X,Y,Z) y objetivo p(t).")
