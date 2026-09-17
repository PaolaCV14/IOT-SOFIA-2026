import cv2
from mediapipe.tasks.python.vision import HandLandmarksConnections, PoseLandmarksConnections

# ==============================================================
# UTILIDADES DE DIBUJO - ESQUELETO Y ARTICULACIONES
# ==============================================================

def dibujar_pose(frame, pose_results, width, height):
    """Dibuja el esqueleto del cuerpo: líneas amarillas y articulaciones naranjas."""
    if not pose_results.pose_landmarks:
        return

    pose = pose_results.pose_landmarks[0]

    # 1. Huesos del cuerpo (Líneas amarillas)
    for conn in PoseLandmarksConnections.POSE_LANDMARKS:
        p1, p2 = pose[conn.start], pose[conn.end]
        pt1 = (int(p1.x * width), int(p1.y * height))
        pt2 = (int(p2.x * width), int(p2.y * height))
        cv2.line(frame, pt1, pt2, (0, 255, 255), 2)

    # 2. Articulaciones (Círculos naranjas)
    for lm in pose:
        cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 4, (0, 200, 255), -1)


def dibujar_manos(frame, hand_results, width, height):
    """Dibuja las manos detectadas: huesos verdes y puntos verde claro."""
    if not hand_results.hand_landmarks:
        return

    for hand in hand_results.hand_landmarks:
        # 1. Huesos de los dedos (Líneas verdes)
        for conn in HandLandmarksConnections.HAND_CONNECTIONS:
            p1, p2 = hand[conn.start], hand[conn.end]
            pt1 = (int(p1.x * width), int(p1.y * height))
            pt2 = (int(p2.x * width), int(p2.y * height))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        # 2. Puntos en cada falange y punta (Círculos verde claro)
        for lm in hand:
            cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 4, (0, 255, 128), -1)