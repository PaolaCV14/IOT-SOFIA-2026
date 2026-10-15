"""
Script para generar las figuras de caracterización experimental (3 paneles y 6 paneles)
para el manuscrito de SOFIA (IEEEtran).

Regenera:
  - fig_current_characterization.pdf / .png (3 paneles: Corriente vs Tiempo)
  - fig_characterization_6panels.pdf / .png (6 paneles: Fila 1 Corriente, Fila 2 Temperatura)
  - Gráficas individuales en alta resolución
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directorios de salida
OUT_DIRS = [
    'paper/Equipo 1 - segundo corte/figures',
    'paper/Equipo 1 - respuesta - segundo corte/figures'
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

# 1. Cargar datos experimentales de las 3 condiciones
df5 = pd.read_csv('docs/experimental-data/datos_5grados.csv')
df90 = pd.read_csv('docs/experimental-data/datos_901.csv')
df_stall = pd.read_csv('docs/experimental-data/datos_CHIDOS_DE_FORZADO.csv')

# Normalizar tiempo desde 0
t5 = df5['Tiempo_s'] - df5['Tiempo_s'].iloc[0]
t90 = df90['Tiempo_s'] - df90['Tiempo_s'].iloc[0]
ts = df_stall['Tiempo_s'] - df_stall['Tiempo_s'].iloc[0]

# Configuración de estilo y tipografía limpia
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

# ==============================================================================
# FIGURA 1: fig_current_characterization (3 paneles de Corriente)
# ==============================================================================
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4.0), dpi=300)

# (a) 5 deg: Max es 582.7 mA. ylim=[0, 650] para que NINGÚN pico quede cortado
ax1.plot(t5, df5['Corriente_mA'], color='#1f77b4', lw=1.3, label='Supply Current $I(t)$')
ax1.set_title(r'(a) Small Error ($e = 5^\circ$ Step)', fontsize=10.5, fontweight='bold')
ax1.set_xlabel('Time (s)', fontsize=9.5)
ax1.set_ylabel('Supply Current (mA)', fontsize=9.5)
ax1.set_xlim([0, 25])
ax1.set_ylim([0, 650])
ax1.axhline(3.1, color='green', linestyle=':', lw=1.2, label='Quiescent ($I_{\\mathrm{quiesc}} = 3.1$ mA)')

# Anotación del pico de inrush
max5_idx = df5['Corriente_mA'].idxmax()
t5_max = t5.iloc[max5_idx]
val5_max = df5['Corriente_mA'].iloc[max5_idx]
ax1.scatter([t5_max], [val5_max], color='red', s=30, zorder=5)
ax1.annotate(f'Inrush Peak: {val5_max:.1f} mA', xy=(t5_max, val5_max), xytext=(t5_max + 2.5, val5_max - 50),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.2), fontsize=8.5, fontweight='bold', color='red')

# Anotación del paso activo a los 18-19s
ax1.annotate('Active Step:\n99.4 mA', xy=(19.28 - 1.03, 99.4), xytext=(12.0, 180),
             arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')
ax1.legend(loc='upper right', fontsize=8)
ax1.grid(True, linestyle='--', alpha=0.5)

# (b) 90 deg: Max es 573.4 mA. ylim=[0, 650]
ax2.plot(t90, df90['Corriente_mA'], color='#ff7f0e', lw=1.3, label='Supply Current $I(t)$')
ax2.set_title(r'(b) Large Error ($e = 90^\circ$ Motion)', fontsize=10.5, fontweight='bold')
ax2.set_xlabel('Time (s)', fontsize=9.5)
ax2.set_ylabel('Supply Current (mA)', fontsize=9.5)
ax2.set_xlim([0, 15])
ax2.set_ylim([0, 650])
ax2.axhline(3.1, color='green', linestyle=':', lw=1.2, label='Quiescent ($I_{\\mathrm{quiesc}} = 3.1$ mA)')

# Anotación pico inrush
max90_idx = df90['Corriente_mA'].idxmax()
t90_max = t90.iloc[max90_idx]
val90_max = df90['Corriente_mA'].iloc[max90_idx]
ax2.scatter([t90_max], [val90_max], color='red', s=30, zorder=5)
ax2.annotate(f'Inrush Peak: {val90_max:.1f} mA', xy=(t90_max, val90_max), xytext=(t90_max - 6.0, val90_max - 50),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.2), fontsize=8.5, fontweight='bold', color='red')

# Anotación tránsito dinámico
ax2.annotate('Dynamic Transit:\n140--172 mA', xy=(8.33 - 1.03, 172.2), xytext=(2.0, 240),
             arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')
ax2.legend(loc='upper right', fontsize=8)
ax2.grid(True, linestyle='--', alpha=0.5)

# (c) Bloqueo mecánico sostenido: Max es 1796.9 mA. ylim=[0, 2000]
ax3.plot(ts, df_stall['Corriente_mA'], color='#d62728', lw=0.7, alpha=0.85, label='Supply Current $I(t)$')
ax3.set_title(r'(c) Mechanical Stall (Locked Rotor)', fontsize=10.5, fontweight='bold')
ax3.set_xlabel('Time (s)', fontsize=9.5)
ax3.set_ylabel('Supply Current (mA)', fontsize=9.5)
ax3.set_xlim([0, 430])
ax3.set_ylim([0, 2000])
ax3.axhline(918.4, color='darkred', linestyle='--', lw=1.3, label='Mean Stall: 918.4 mA')

# Anotación pico transitorio máximo
maxs_idx = df_stall['Corriente_mA'].idxmax()
ts_max = ts.iloc[maxs_idx]
vals_max = df_stall['Corriente_mA'].iloc[maxs_idx]
ax3.scatter([ts_max], [vals_max], color='darkred', s=35, zorder=5)
ax3.annotate(f'Max Surge: {vals_max:.1f} mA', xy=(ts_max, vals_max), xytext=(ts_max - 190, vals_max - 160),
             arrowprops=dict(arrowstyle='->', color='darkred', lw=1.2), fontsize=8.5, fontweight='bold', color='darkred')
ax3.legend(loc='upper right', fontsize=8)
ax3.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

for d in OUT_DIRS:
    fig.savefig(f'{d}/fig_current_characterization.png', dpi=300)
    fig.savefig(f'{d}/fig_current_characterization.pdf')
plt.close(fig)
print('Saved fig_current_characterization.')

# ==============================================================================
# FIGURA 2: fig_characterization_6panels (2 filas x 3 columnas: Corriente + Temperatura)
# Corregido con escala completa sin ningún corte ni texto encimado
# ==============================================================================
fig6, axs = plt.subplots(2, 3, figsize=(15, 7.8), dpi=300)

# ----------------- Fila 0: Corrientes (sin cortes de picos) -----------------
# (a1) 5 deg corriente
axs[0, 0].plot(t5, df5['Corriente_mA'], color='#1f77b4', lw=1.3, label='$I(t)$')
axs[0, 0].set_title(r'(a1) Small Error ($e = 5^\circ$): Current', fontsize=10.5, fontweight='bold')
axs[0, 0].set_xlabel('Time (s)', fontsize=9)
axs[0, 0].set_ylabel('Supply Current (mA)', fontsize=9)
axs[0, 0].set_xlim([0, 25])
axs[0, 0].set_ylim([0, 650])  # Pico de 582.7 mA visible!
axs[0, 0].axhline(3.1, color='green', linestyle=':', lw=1.2, label='Quiescent: 3.1 mA')
axs[0, 0].scatter([t5_max], [val5_max], color='red', s=25, zorder=5)
axs[0, 0].annotate(f'Inrush: {val5_max:.1f} mA', xy=(t5_max, val5_max), xytext=(t5_max + 2.5, val5_max - 50),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.1), fontsize=8, color='red', fontweight='bold')
axs[0, 0].annotate('Step: 99.4 mA', xy=(19.28 - 1.03, 99.4), xytext=(11.5, 180),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8, fontweight='bold')
axs[0, 0].legend(loc='upper right', fontsize=8)

# (b1) 90 deg corriente
axs[0, 1].plot(t90, df90['Corriente_mA'], color='#ff7f0e', lw=1.3, label='$I(t)$')
axs[0, 1].set_title(r'(b1) Large Error ($e = 90^\circ$): Current', fontsize=10.5, fontweight='bold')
axs[0, 1].set_xlabel('Time (s)', fontsize=9)
axs[0, 1].set_ylabel('Supply Current (mA)', fontsize=9)
axs[0, 1].set_xlim([0, 15])
axs[0, 1].set_ylim([0, 650])  # Pico de 573.4 mA visible!
axs[0, 1].axhline(3.1, color='green', linestyle=':', lw=1.2, label='Quiescent: 3.1 mA')
axs[0, 1].scatter([t90_max], [val90_max], color='red', s=25, zorder=5)
axs[0, 1].annotate(f'Inrush: {val90_max:.1f} mA', xy=(t90_max, val90_max), xytext=(t90_max - 6.0, val90_max - 50),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.1), fontsize=8, color='red', fontweight='bold')
axs[0, 1].annotate('Transit: 172 mA', xy=(8.33 - 1.03, 172.2), xytext=(2.0, 240),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8, fontweight='bold')
axs[0, 1].legend(loc='upper right', fontsize=8)

# (c1) Bloqueo corriente
axs[0, 2].plot(ts, df_stall['Corriente_mA'], color='#d62728', lw=0.7, alpha=0.85, label='$I(t)$')
axs[0, 2].set_title(r'(c1) Locked Rotor: Current', fontsize=10.5, fontweight='bold')
axs[0, 2].set_xlabel('Time (s)', fontsize=9)
axs[0, 2].set_ylabel('Supply Current (mA)', fontsize=9)
axs[0, 2].set_xlim([0, 430])
axs[0, 2].set_ylim([0, 2000]) # Pico de 1796.9 mA visible!
axs[0, 2].axhline(918.4, color='darkred', linestyle='--', lw=1.3, label='Mean Stall: 918.4 mA')
axs[0, 2].scatter([ts_max], [vals_max], color='darkred', s=30, zorder=5)
axs[0, 2].annotate(f'Peak: {vals_max:.1f} mA', xy=(ts_max, vals_max), xytext=(ts_max - 190, vals_max - 170),
                   arrowprops=dict(arrowstyle='->', color='darkred', lw=1.1), fontsize=8, color='darkred', fontweight='bold')
axs[0, 2].legend(loc='upper right', fontsize=8)

# ----------------- Fila 1: Temperaturas -----------------
# (a2) 5 deg temperatura
axs[1, 0].plot(t5, df5['Temperatura_C'], color='#2ca02c', lw=1.4, label='Measured $T_s(t)$')
axs[1, 0].set_title(r'(a2) Small Error ($e = 5^\circ$): Temperature', fontsize=10.5, fontweight='bold')
axs[1, 0].set_xlabel('Time (s)', fontsize=9)
axs[1, 0].set_ylabel(r'Temperature ($^\circ$C)', fontsize=9)
axs[1, 0].set_xlim([0, 60])
axs[1, 0].set_ylim([25.0, 28.5])
axs[1, 0].axhline(df5['Temperatura_C'].iloc[0], color='gray', linestyle=':', label=rf'Initial: {df5["Temperatura_C"].iloc[0]:.1f} $^\circ$C')
axs[1, 0].legend(loc='lower right', fontsize=8)

# (b2) 90 deg temperatura
axs[1, 1].plot(t90, df90['Temperatura_C'], color='#2ca02c', lw=1.4, label='Measured $T_s(t)$')
axs[1, 1].set_title(r'(b2) Large Error ($e = 90^\circ$): Temperature', fontsize=10.5, fontweight='bold')
axs[1, 1].set_xlabel('Time (s)', fontsize=9)
axs[1, 1].set_ylabel(r'Temperature ($^\circ$C)', fontsize=9)
axs[1, 1].set_xlim([0, 70])
axs[1, 1].set_ylim([27.5, 31.5])
axs[1, 1].axhline(df90['Temperatura_C'].iloc[0], color='gray', linestyle=':', label=rf'Initial: {df90["Temperatura_C"].iloc[0]:.1f} $^\circ$C')
axs[1, 1].legend(loc='lower right', fontsize=8)

# (c2) Bloqueo temperatura
max_temp_idx = df_stall['Temperatura_C'].idxmax()
max_temp_t = ts.iloc[max_temp_idx]
max_temp_val = df_stall['Temperatura_C'].iloc[max_temp_idx]

axs[1, 2].plot(ts, df_stall['Temperatura_C'], color='#9467bd', lw=1.4, label='Measured $T_s(t)$')
axs[1, 2].set_title(r'(c2) Locked Rotor: Temperature', fontsize=10.5, fontweight='bold')
axs[1, 2].set_xlabel('Time (s)', fontsize=9)
axs[1, 2].set_ylabel(r'Temperature ($^\circ$C)', fontsize=9)
axs[1, 2].set_xlim([0, 430])
axs[1, 2].set_ylim([30.0, 47.0])
axs[1, 2].axhline(df_stall['Temperatura_C'].iloc[0], color='gray', linestyle=':', label=rf'Initial: {df_stall["Temperatura_C"].iloc[0]:.1f} $^\circ$C')
axs[1, 2].scatter([max_temp_t], [max_temp_val], color='purple', s=30, zorder=5)
axs[1, 2].annotate(rf'Peak: {max_temp_val:.1f} $^\circ$C', xy=(max_temp_t, max_temp_val), xytext=(max_temp_t - 160, max_temp_val - 3.5),
                   arrowprops=dict(arrowstyle='->', color='purple', lw=1.1), fontsize=8.5, fontweight='bold', color='purple')
axs[1, 2].legend(loc='lower right', fontsize=8)

for ax in axs.flat:
    ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

for d in OUT_DIRS:
    fig6.savefig(f'{d}/fig_characterization_6panels.png', dpi=300)
    fig6.savefig(f'{d}/fig_characterization_6panels.pdf')
plt.close(fig6)
print('Saved fig_characterization_6panels (all 6 panels perfectly scaled).')
