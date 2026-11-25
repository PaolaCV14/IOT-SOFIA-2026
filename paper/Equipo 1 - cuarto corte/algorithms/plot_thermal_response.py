#!/usr/bin/env python3
"""
Generador de Fig. 1 (fig_thermal_response.pdf / .png):
Caracterización térmica experimental del servomotor MG90S (Trials 1 y 2),
incluyendo:
  (a) Trial 1: Curva medida, pendiente media (226 s, beta=0.214 °C/s) y pendiente inicial (0-60 s, 0.111 °C/s) + residuos.
  (b) Trial 2: Curva medida en t_DAQ in [973.1, 1654.1] s y ajuste NLLS de Ec. (5) sobre el tramo de bloqueo
      t_DAQ in [1053.1, 1445.1] s (Ta=19.73 °C, dT_inf=160.8 +/- 13.5 °C, tau_T=1011.4 +/- 98.2 s) + residuos.
"""

import os
import openpyxl
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 10.5,
    'legend.fontsize': 8.2,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'mathtext.fontset': 'stix',
})

EXCEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../documents/servo_characterization.xlsx")
)
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../figures"))
RESP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Equipo 1 - respuesta - tercer corte/figures"))

wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

# 1. Trial 1 (ROTO 1)
s1 = wb['ROTO 1']
t1, ang1, temp1 = [], [], []
for r in range(2, s1.max_row + 1):
    vt, vang, vtemp = s1.cell(r, 1).value, s1.cell(r, 2).value, s1.cell(r, 3).value
    if vt is not None and vtemp is not None:
        t1.append(float(vt))
        ang1.append(float(vang) if vang is not None else 180.0)
        temp1.append(float(vtemp))

t1 = np.array(t1)
temp1 = np.array(temp1)
t1_rel = t1 - t1[0]

# Regresión lineal media (0-225 s) y primeros 60 s
beta_mean1, T0_1 = np.polyfit(t1_rel, temp1, 1)
temp1_fit = T0_1 + beta_mean1 * t1_rel
res1 = temp1 - temp1_fit
r2_1 = 1.0 - np.sum(res1 ** 2) / np.sum((temp1 - np.mean(temp1)) ** 2)
rmse1 = np.sqrt(np.mean(res1 ** 2))

mask60 = t1_rel <= 60.0
beta_init60, T0_60 = np.polyfit(t1_rel[mask60], temp1[mask60], 1)

# 2. Trial 2 (Hoja2)
s2 = wb['Hoja2']
t2, ang2, temp2 = [], [], []
for r in range(2, s2.max_row + 1):
    vt, vang, vtemp = s2.cell(r, 1).value, s2.cell(r, 2).value, s2.cell(r, 3).value
    if vt is not None and vtemp is not None:
        t2.append(float(vt))
        ang2.append(float(vang) if vang is not None else 180.0)
        temp2.append(float(vtemp))

t2 = np.array(t2)
ang2 = np.array(ang2)
temp2 = np.array(temp2)

# Tramo de bloqueo activo: desde t_DAQ = 1053.1 s hasta el pico (1445.1 s)
idx_start = int(np.where(t2 >= 1053.1)[0][0])
idx_peak2 = int(np.argmax(temp2))
Ta_2 = float(np.mean(temp2[(t2 >= 1023.1) & (t2 <= 1053.1)]))  # 19.73 °C

ts_seg = t2[idx_start:idx_peak2 + 1] - t2[idx_start]
Ts_seg = temp2[idx_start:idx_peak2 + 1]
dT_seg = Ts_seg - Ta_2


def first_order_step(t, dT_inf, tau_T):
    return dT_inf * (1.0 - np.exp(-t / tau_T))


popt, pcov = curve_fit(first_order_step, ts_seg, dT_seg, p0=[120.0, 800.0], maxfev=20000)
dT_inf_fit, tau_T_fit = popt[0], popt[1]
ci95 = 1.96 * np.sqrt(np.diag(pcov))

temp2_nlls = Ta_2 + first_order_step(ts_seg, dT_inf_fit, tau_T_fit)
res2 = Ts_seg - temp2_nlls
r2_2 = 1.0 - np.sum(res2 ** 2) / np.sum((Ts_seg - np.mean(Ts_seg)) ** 2)
rmse2 = np.sqrt(np.mean(res2 ** 2))

fig = plt.figure(figsize=(7.1, 3.75), dpi=300)
gs = GridSpec(2, 2, height_ratios=[2.45, 1.0], hspace=0.18, wspace=0.22)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax1_res = fig.add_subplot(gs[1, 0], sharex=ax1)
ax2_res = fig.add_subplot(gs[1, 1], sharex=ax2)

# --- (a) Trial 1 ---
ax1.plot(t1_rel, temp1, color='#d9534f', lw=1.6, label=r'Measured $T_s(t)$')
ax1.plot(t1_rel, temp1_fit, color='#1f2937', linestyle='--', lw=1.35,
         label=rf'Mean rate ($\bar{{\beta}} = {beta_mean1:.3f}\,^\circ\mathrm{{C/s}}$, $R^2={r2_1:.3f}$)')
ax1.plot(t1_rel[mask60], T0_60 + beta_init60 * t1_rel[mask60], color='#0284c7', linestyle='-.', lw=1.4,
         label=rf'Initial $0\text{{--}}60\,\mathrm{{s}}$ ($\beta_0 = {beta_init60:.3f}\,^\circ\mathrm{{C/s}}$)')
ax1.scatter([t1_rel[-1]], [temp1[-1]], color='#900C3F', s=30, zorder=5,
            label=rf'Peak $T_{{\max}} = {temp1[-1]:.2f}\,^\circ\mathrm{{C}}$')
ax1.set_title(r'(a) Trial 1: Stall Heating & Linear Rates', fontweight='bold')
ax1.set_ylabel(r'Temperature ($^\circ\mathrm{C}$)')
ax1.set_xlim([0, 235])
ax1.set_ylim([18, 70])
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='lower right', framealpha=0.92)
plt.setp(ax1.get_xticklabels(), visible=False)

ax1_res.plot(t1_rel, res1, color='#d9534f', lw=1.05)
ax1_res.axhline(0, color='black', linestyle=':', lw=0.9)
ax1_res.set_xlabel(r'Elapsed Time $t$ ($\mathrm{s}$)')
ax1_res.set_ylabel(r'Resid. ($^\circ\mathrm{C}$)')
ax1_res.set_ylim([-3.5, 3.5])
ax1_res.grid(True, linestyle='--', alpha=0.5)
ax1_res.text(0.04, 0.74, rf'OLS RMSE $= {rmse1:.2f}\,^\circ\mathrm{{C}}$',
             transform=ax1_res.transAxes, fontsize=8.5)

# --- (b) Trial 2 ---
ax2.plot(t2, temp2, color='#0275d8', lw=1.5, label=r'Measured $T_s(t)$')
ax2.plot(t2[idx_start:idx_peak2 + 1], temp2_nlls, color='#1f2937', linestyle='--', lw=1.4,
         label=rf'NLLS Fit ($\tau_T={tau_T_fit:.0f}\pm{ci95[1]:.0f}\,\mathrm{{s}}$, $R^2={r2_2:.3f}$)')
ax2.scatter([t2[idx_peak2]], [temp2[idx_peak2]], color='#003366', s=30, zorder=5,
            label=rf'Inflection Peak $T_{{\max}} = {temp2[idx_peak2]:.2f}\,^\circ\mathrm{{C}}$')
ax2.axvline(t2[idx_start], color='gray', linestyle=':', lw=1.0)
ax2.axvline(t2[idx_peak2], color='gray', linestyle=':', lw=1.0)
ax2.set_title(r'(b) Trial 2: Stall Window ($1053\text{--}1445\,\mathrm{s}$) & Cooling', fontweight='bold')
ax2.set_ylabel(r'Temperature ($^\circ\mathrm{C}$)')
ax2.set_xlim([965, 1665])
ax2.set_ylim([18, 75])
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='lower right', framealpha=0.92)
plt.setp(ax2.get_xticklabels(), visible=False)

ax2_res.plot(t2[idx_start:idx_peak2 + 1], res2, color='#0275d8', lw=1.05)
ax2_res.axhline(0, color='black', linestyle=':', lw=0.9)
ax2_res.set_xlabel(r'DAQ Timestamp $t$ ($\mathrm{s}$)')
ax2_res.set_ylabel(r'Resid. ($^\circ\mathrm{C}$)')
ax2_res.set_ylim([-3.5, 3.5])
ax2_res.grid(True, linestyle='--', alpha=0.5)
ax2_res.text(0.04, 0.74, rf'NLLS RMSE $= {rmse2:.2f}\,^\circ\mathrm{{C}}$ ($1053\text{{--}}1445\,\mathrm{{s}}$)',
             transform=ax2_res.transAxes, fontsize=8.5)

fig.subplots_adjust(left=0.08, right=0.98, top=0.91, bottom=0.13)

for d in [OUTPUT_DIR, RESP_DIR]:
    os.makedirs(d, exist_ok=True)
    fig.savefig(os.path.join(d, "fig_thermal_response.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_thermal_response.pdf"))

print(f"OK: Trial 1 beta_mean={beta_mean1:.4f}, beta_0_60={beta_init60:.4f}; Trial 2 NLLS dT_inf={dT_inf_fit:.1f}+/-{ci95[0]:.1f}, tau_T={tau_T_fit:.1f}+/-{ci95[1]:.1f}, R2={r2_2:.4f}, RMSE={rmse2:.2f}")
