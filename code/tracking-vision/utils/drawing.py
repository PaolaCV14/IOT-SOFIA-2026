# ==============================================================
# DIBUJO DE PUNTOS Y ESQUELETOS SOBRE LA IMAGEN
# Dibuja las líneas y círculos sobre el frame de OpenCV
# para que el usuario pueda ver sus manos y cuerpo en la ventana.
# ==============================================================

import cv2
from mediapipe.tasks.python.vision import HandLandmarksConnections, PoseLandmarksConnections

def dibujar_pose(frame, pose_results, width, height):
    """Dibuja el cuerpo: líneas amarillas y articulaciones naranjas."""
    if not pose_results.pose_landmarks:
        return

    pose = pose_results.pose_landmarks[0]

    # 1. Conexiones del cuerpo (hombros, brazos, torso)
    for conn in PoseLandmarksConnections.POSE_LANDMARKS:
        p1, p2 = pose[conn.start], pose[conn.end]
        pt1 = (int(p1.x * width), int(p1.y * height))
        pt2 = (int(p2.x * width), int(p2.y * height))
        cv2.line(frame, pt1, pt2, (0, 255, 255), 2)

    # 2. Círculos en cada articulación
    for lm in pose:
        cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 4, (0, 200, 255), -1)


def dibujar_manos(frame, hand_results, width, height):
    """Dibuja las manos: líneas verdes entre falanges y círculos en las puntas."""
    if not hand_results.hand_landmarks:
        return

    for hand in hand_results.hand_landmarks:
        # 1. Huesos de los dedos
        for conn in HandLandmarksConnections.HAND_CONNECTIONS:
            p1, p2 = hand[conn.start], hand[conn.end]
            pt1 = (int(p1.x * width), int(p1.y * height))
            pt2 = (int(p2.x * width), int(p2.y * height))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        # 2. Puntos de cada nudillo y punta de dedo
        for lm in hand:
            cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 4, (0, 255, 128), -1)