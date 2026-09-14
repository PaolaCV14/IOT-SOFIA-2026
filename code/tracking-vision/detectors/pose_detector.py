import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseDetector:

    def __init__(
        self,
        model_path="models/pose_landmarker_lite.task"
    ):

        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.detector = vision.PoseLandmarker.create_from_options(
            options
        )

    def detect(self, image, timestamp_ms):
        return self.detector.detect_for_video(
            image,
            timestamp_ms
        )

    def close(self):
        self.detector.close()