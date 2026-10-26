"""
Secuencia de gestos de SOFIA - sofia_controller_gestos.
Controlador Webots con State Machine formal: ESPERA -> MOVER -> ASENTAR -> SOSTENER.

Integra:
- El modelo cinemático y dinámico con Rate Limiter (W_MAX, V_MAX, D_MAX, TOL).
- El espejo mecánico de articulaciones de SOFIA: joint_3 como espejo de joint_2.
- Telemetría en tiempo real: robot.setCustomData().
- Catálogo completo unificado: gestos del profesor ('si', 'no', 'ola') y gestos
  de visión artificial / ESP32 de SOFÍA ('saludo', 'corazon', 'ppt_conteo', 'swipe').
"""

from controller import Robot

robot = Robot()
dt_ms = int(robot.getBasicTimeStep())
dt = dt_ms / 1000.0

# 1. Motores y Sensores (sofia.proto)
q1 = robot.getDevice('joint_1')
q2 = robot.getDevice('joint_2')
q3 = robot.getDevice('joint_3')  # Mecánicamente espejo de q2

s1 = robot.getDevice('joint_1_sensor')
s2 = robot.getDevice('joint_2_sensor')
s1.enable(dt_ms)
s2.enable(dt_ms)

# 2. Control y Dinámica (W_MAX de sofia.proto)
W_MAX = 10.471976   # Velocidad máxima del motor [rad/s]
V_MAX = 1.5         # Velocidad máxima del comando [rad/s]
D_MAX = V_MAX * dt  # Variación máxima del comando por paso [rad]
TOL = 0.01          # Tolerancia de convergencia de los sensores [rad]

q1.setVelocity(W_MAX)
q2.setVelocity(W_MAX)
q3.setVelocity(W_MAX)

# 3. Tarea y Poses
T_ESPERA = 2.0      # Espera entre comandos [s]
T_SOSTENER = 1.0    # Tiempo que se sostiene la última pose [s]
NEUTRO = (0.0, 0.0)

# Poses (q1, q2) de cada gesto [rad]
GESTOS = {
    # Gestos base del profesor
    'si':         [(0.0, 0.45), (0.0, -0.25), (0.0, 0.45)],
    'no':         [(0.45, 0.0), (-0.45, 0.0), (0.45, 0.0)],
    'ola':        [(0.40, 0.0), (0.0, 0.40), (-0.40, 0.0)],
    # Gestos propios de SOFÍA (Visión MediaPipe y ESP32)
    'saludo':     [(0.0, -0.52), (0.0, 0.52), (0.0, -0.52), (0.0, 0.52)],  # 3 ciclos entre [90, 60] y [90, 120]
    'corazon':    [(0.0, 0.52), (0.52, 0.0), (0.0, -0.52), (-0.52, 0.0)],  # Órbita de 4 cuadrantes
    'ppt_conteo': [(0.0, 0.35), (0.0, -0.20), (0.0, 0.35), (0.0, -0.20)], # 1-2-3 ritmo de juego
    'swipe_der':  [(0.52, 0.0)],                                            # Barrido a la derecha
    'swipe_izq':  [(-0.52, 0.0)],                                           # Barrido a la izquierda
}

comandos = ['saludo', 'si', 'no', 'corazon']  # Cola de comandos de prueba

# 4. Memoria de la Máquina de Estados
ESPERA = 'ESPERA'
MOVER = 'MOVER'
ASENTAR = 'ASENTAR'
SOSTENER = 'SOSTENER'

estado = ESPERA
t_entrada = 0.0
gesto = None
ruta = []
al_terminar = None
y1, y2 = NEUTRO

def ruta_gesto(g):
    return list(GESTOS[g])

def ruta_a_neutro():
    return [NEUTRO]

def saturar(u, u_max):
    return max(-u_max, min(u_max, u))

def errores(p1, p2):
    """e_y: falta al comando; e_p: falta al servo [rad]."""
    if not ruta:
        return 0.0, 0.0
    r1, r2 = ruta[0]
    return max(abs(r1 - y1), abs(r2 - y2)), max(abs(r1 - p1), abs(r2 - p2))

def cambiar(nuevo, t, p1, p2):
    global estado, t_entrada
    detalle = f'gesto {gesto}' if gesto else 'sin gesto'
    print(f'[{t:6.2f} s] {estado} -> {nuevo}  ({detalle}; q1={p1:+.2f}, q2={p2:+.2f})')
    estado = nuevo
    t_entrada = t
    robot.setCustomData(f'{estado} ({detalle})')    # Telemetría hacia Webots

# 5. Bucle de Ejecución
robot.setCustomData(f'{estado} (sin gesto)')
while robot.step(dt_ms) != -1:
    t = robot.getTime()
    p1, p2 = s1.getValue(), s2.getValue()
    t_estado = t - t_entrada

    e_y, e_p = errores(p1, p2)

    # 1) Transiciones
    if estado == ESPERA and t_estado >= T_ESPERA and comandos:
        gesto = comandos.pop(0)
        ruta = ruta_gesto(gesto)
        al_terminar = SOSTENER
        cambiar(MOVER, t, p1, p2)

    elif estado == MOVER and e_y < 1e-6:
        cambiar(ASENTAR, t, p1, p2)

    elif estado == ASENTAR and e_p < TOL:
        ruta.pop(0)
        if not ruta and al_terminar == ESPERA:
            gesto = None
        cambiar(MOVER if ruta else al_terminar, t, p1, p2)

    elif estado == SOSTENER and t_estado >= T_SOSTENER:
        ruta = ruta_a_neutro()
        al_terminar = ESPERA
        cambiar(MOVER, t, p1, p2)

    # 2) Acciones: interpolación suave con Rate Limiter
    if estado == MOVER and ruta:
        r1, r2 = ruta[0]
        y1 += saturar(r1 - y1, D_MAX)
        y2 += saturar(r2 - y2, D_MAX)

    # Actuación de motores (joint_3 copia fielmente a joint_2)
    q1.setPosition(y1)
    q2.setPosition(y2)
    q3.setPosition(y2)
