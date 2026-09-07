import cv2
import mediapipe as mp

# 1. Le decimos a MediaPipe que queremos usar su módulo de Manos
mp_hands = mp.solutions.hands

# 2. Configuramos el detector. 
# min_detection_confidence=0.7 significa que debe estar 70% seguro de que es una mano para no seguir sombras a lo güey.
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1 # Solo nos interesa 1 mano para que los paneles la sigan
)

# 3. Utilidad para dibujar los puntitos del esqueleto en pantalla
mp_drawing = mp.solutions.drawing_utils

# 4. Prendemos la cámara web (el 0 suele ser la cámara por defecto de la laptop)
cap = cv2.VideoCapture(0)