# Bitácora de Correcciones — Cuarto Corte (SOFIA)

**Proyecto:** SOFIA — Modular Robotic Kinetic Surface for Human-Robot Interaction and Thermal-Constrained Actuator Characterization  
**Repositorio:** `https://github.com/PaolaCV14/IOT-SOFIA-2026` (rama `main`, etiqueta `v0.4.0`)  
**Entregable:** `paper/Equipo 1 - cuarto corte/Equipo 1 - cuarto corte.tex` (10 páginas, formato IEEEtran) y carta de respuesta `paper/Equipo 1 - respuesta - cuarto corte/Equipo 1 - respuesta - cuarto corte.tex` (4 páginas).

---

## 1. Verificación de Estructura IEEE Completa

Se verificó la presencia e integridad de las 6 secciones y todos los apartados generales requeridos:
- **General:** `Title`, `Authors`, `Abstract`, `Index Terms` (`IEEEkeywords`), `Author Contributions`, `Data Availability`, `Acknowledgment`, `Declaration of Generative AI`, `Conflicts of Interest`, y `References`.
- **Secciones:**
  1. `I. Introduction`
  2. `II. Materials and Methods`
  3. `III. Design and Implementation of the Technological Solution`
  4. `IV. Results`
  5. `V. Discussion`
  6. `VI. Conclusions`

---

## 2. Registro de Cambios por Observación (R1.1–R4.6)

| Obs. | Estado | Cambios realizados en el artículo y archivos de respaldo |
| :--- | :--- | :--- |
| **R1.1** | Atendida | Se restauró íntegramente `IEEEtran.cls` eliminando del preámbulo `\linespread{0.91}`, `\fontsize{9.5pt}` y ajustes manuales de flotantes/ecuaciones. Para ajustar a **10 páginas** sin perder contenido técnico: se compactaron filas de Tabla III (`tab:bom_sofia`) y Tabla V (`tab:compliance`), se fusionó el cableado en Tabla VI (`tab:power_balance`), se pasó Fig. 8 (`fig:sofia_pcb_design`) a una columna, se ajustaron alturas de Figs. 5, 9, 10 y 11, y se eliminaron repeticiones entre *Results*, *Discussion*, *Conclusions* y pies de figura. |
| **R1.2** | Atendida | Se añadieron las citas y descripciones de Fig. 3 (`fig:sofia_mechanical_design`) en *Mechanical Design and Assembly* y de Fig. 6 (`fig:maquina_estado_sofia`) en `sec:teleoperation_pipeline`. |
| **R1.3** | Atendida | En Fig. 5 (`fig:sofia_simulation`) se dejaron 3 cuadros legibles (`fig_sim_1`, `fig_sim_3`, `fig_sim_5` a `0.22\textwidth`); Fig. 6 se reconstruyó en `TikZ` y se reposicionaron etiquetas diagonales en Figs. 6 y 7 para evitar traslapes; Fig. 11 (`modulo_fisico` + `SALUDO`) se presentó en 3 subfiguras sin recorte vertical. |
| **R2.1** | Atendida | Se moderaron las afirmaciones excedentes: `"100% rejection"` → `"single 60-transition run"` (Tabla XI); `"stress-tested immunity"` → `"single-run immunity checks"` (Abstract); `"repeatable thermal signature"` → `"sustained Joule heating with a 4× inter-trial rate dispersion"` (Conclusiones); `"integrating 30 FPS"` → `"designed for 30 FPS"`; y se aclaró en Sec. III-F que el corte `INA219` está *Pending*. |
| **R2.2** | Atendida | Se reemplazó `"inflection peak"` por `"peak temperature at stall release"` en Abstract, Sec. IV-A, Sec. V-A y en la leyenda de Fig. 9(b) (`plot_thermal_response.py`). |
| **R2.3** | Atendida | Se eliminó el presupuesto de `$158 USD` y cifras no trazadas de inFORM/Transform en *Discussion*, así como cifras de latencia/FPS no medidas en *Conclusions*. |
| **R3.1** | Atendida | En Sec. III-F (`sec:risk_mitigation`) se adoptó la **Opción A** verificada en firmware (temporizador conservador de `15 s` para `|Δq| ≤ 2°` **sin exclusión en `q = 90°`**, suspendiendo PWM con `STOP` y reactivándose ante `|Δq| > 2°`), separando la **Opción B** (`INA219` `I_bank > I_base + 0.5 A`) como provisión *Pending* de la PCB completa; el umbral de banco se fijó en `3.40 A` (`>2 s`, detectando `≥ 4` bloqueos) y Tabla IX se actualizó a `INA219 trip pending`. |
| **R3.2** | Atendida | Se eliminó la atribución no demostrada de la dispersión `4×`, se incorporó la **Tabla X** (`tab:trial_conditions`) con condiciones por sesión, se corrigió `T0 = 21.37 °C` en Trial 1, se explicó la aceleración `0.111 → 0.223 °C/s` tras `60 s` como degradación progresiva, y se aclaró en texto y en Fig. 9 (`plot_thermal_response.py`) que el ajuste NLLS es meramente descriptivo por colinealidad de `(ΔT_∞, τ_T)`. |
| **R3.3** | Atendida | En Sec. II (`ln:servo-exp`) se añadió la derivación completa `τ_req = Jα + m_f g r_cg + τ_fric ≈ 0.45 kgf·cm` (`α ≈ 419 rad/s²`, `J ≈ 1.36e-5 kg·m²`). |
| **R3.4** | Atendida | En Tabla VI (`tab:power_balance`) se corrigió la longitud de rama a `0.70 m RT` (`2 × 0.35 m`) y total `2.20 m RT`, consistente con `37.1 mΩ` y `ΔV = 0.064 V`. |
| **R4.1** | Atendida | Se eliminaron cifras sin registro (`43.1 ms`, `137/140`, `registro_estres_errores.csv`), se marcó el enlace BLE RTT como `Pending` en Tabla V, y se corrigió Sec. IV-D a **10 de 14** especificaciones satisfechas y **4 pendientes** (aclarando verificación parcial de `REQ-COM` y `REQ-SAF`). Además, en Fig. 10 (`plot_characterization_figures.py`) se alineó el título `(a)` (`Noise & 14° Step`) y la media `(c)` (`861.8 mA` en `[39, 311] s`). |
| **R4.2** | Atendida | Se separó el resultado medido (`≈ 180 s` lineal desde ambiente a `60 °C` bajo `0.2143 °C/s`) de la decisión de diseño (`Δt ≤ 15 s`, margen `12×`, `ΔT ≤ 3.2 °C`). |
| **R4.3** | Atendida | En Sec. IV-B y Tabla XI se aclaró que `MAE = 0.00°` en el cono `±30°` verifica consistencia algebraica (*Sim. Implementation*) y que la precisión física queda sujeta a la prueba óptica a `60 FPS` (*Pending*). |
| **R4.4** | Atendida | Se reescribieron los objetivos 1, 2 y 4 de la Introducción con criterios previos de ingeniería (`R² ≥ 0.95`, `T_s ≤ 60 °C`, `MAE ≤ 5°`) sin copiar resultados experimentales. |
| **R4.5** | Atendida | Se unificó *Data Availability* al repositorio público `https://github.com/PaolaCV14/IOT-SOFIA-2026` (rama `main`, tag `v0.4.0`), y se retiraron ligas personales de OneDrive de `docs/MANUAL_DE_USUARIO.md` y `docs/EVIDENCIA_PRUEBAS_Y_MANEJO_ERRORES.md`. |
| **R4.6** | Atendida | Se añadió la columna **Evid.** en Tabla V clasificando cada requisito como `Datasheet`, `Measured`, `Meas.+DS` o `Pending`. |
