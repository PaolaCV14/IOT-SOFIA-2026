import cv2

from mediapipe.tasks.python.vision import (
    HandLandmarksConnections,
    PoseLandmarksConnections
)


def dibujar_pose(frame, pose_results, width, height):

    if not pose_results.pose_landmarks:
        return

    pose = pose_results.pose_landmarks[0]

    # Conexiones del cuerpo
    for conn in PoseLandmarksConnections.POSE_LANDMARKS:

        pt1 = pose[conn.start]
        pt2 = pose[conn.end]

        cv2.line(
            frame,
            (
                int(pt1.x * width),
                int(pt1.y * height)
            ),
            (
                int(pt2.x * width),
                int(pt2.y * height)
            ),
            (0, 255, 255),
            2
        )

    # Puntos del cuerpo
    for landmark in pose:

        cv2.circle(
            frame,
            (
                int(landmark.x * width),
                int(landmark.y * height)
            ),
            4,
            (0, 200, 255),
            -1
        )


def dibujar_manos(frame, hand_results, width, height):

    if not hand_results.hand_landmarks:
        return

    for hand in hand_results.hand_landmarks:

        # Conexiones de los dedos
        for conn in HandLandmarksConnections.HAND_CONNECTIONS:

            pt1 = hand[conn.start]
            pt2 = hand[conn.end]

            cv2.line(
                frame,
                (
                    int(pt1.x * width),
                    int(pt1.y * height)
                ),
                (
                    int(pt2.x * width),
                    int(pt2.y * height)
                ),
                (0, 255, 0),
                2
            )

        # Puntos de los dedos
        for landmark in hand:

            cv2.circle(
                frame,
                (
                    int(landmark.x * width),
                    int(landmark.y * height)
                ),
                4,
                (0, 255, 128),
                -1
            )