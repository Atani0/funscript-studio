from __future__ import annotations

from typing import Dict, Optional, Tuple

from .frame_sampler import FrameSample
from .perception_schema import clamp01


class VisualAnalyzer:
    def __init__(self) -> None:
        self.previous_gray = None
        self.previous_motion = 0.0

    def analyze(self, sample: FrameSample) -> Dict[str, object]:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            return self._empty(sample.timestamp_ms)

        frame = sample.image
        if frame is None:
            return self._empty(sample.timestamp_ms)
        resized = cv2.resize(frame, (160, 90))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        edges = cv2.Canny(gray, 80, 160)
        edge_density = float(np.mean(edges > 0))
        saturation = float(np.mean(hsv[:, :, 1])) / 255.0
        texture_complexity = float(np.std(gray)) / 128.0
        skin_likelihood = self._skin_likelihood(resized)

        motion = 0.0
        region = {"x": 0.35, "y": 0.35, "w": 0.3, "h": 0.3}
        scene_change = False
        if self.previous_gray is not None:
            diff = cv2.absdiff(gray, self.previous_gray)
            motion = clamp01(float(np.mean(diff)) / 45.0)
            scene_change = motion > 0.72
            region = self._motion_region(diff)
        smoothness = clamp01(1.0 - abs(motion - self.previous_motion))
        self.previous_gray = gray
        self.previous_motion = motion

        return {
            "time": sample.timestamp_ms,
            "motion": motion,
            "scene_change": scene_change,
            "main_motion_region": region,
            "frame_features": {
                "edge_density": clamp01(edge_density),
                "saturation": clamp01(saturation),
                "texture_complexity": clamp01(texture_complexity),
                "skin_likelihood": clamp01(skin_likelihood),
                "motion_smoothness": smoothness,
            },
        }

    def _empty(self, time_ms: int) -> Dict[str, object]:
        return {
            "time": time_ms,
            "motion": 0.0,
            "scene_change": False,
            "main_motion_region": {"x": 0.35, "y": 0.35, "w": 0.3, "h": 0.3},
            "frame_features": {},
        }

    def _skin_likelihood(self, frame) -> float:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            lower = np.array([0, 133, 77], dtype=np.uint8)
            upper = np.array([255, 173, 127], dtype=np.uint8)
            mask = cv2.inRange(ycrcb, lower, upper)
            return float(np.mean(mask > 0))
        except Exception:
            return 0.0

    def _motion_region(self, diff) -> Dict[str, float]:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
            _, mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
            points = cv2.findNonZero(mask)
            if points is None:
                return {"x": 0.35, "y": 0.35, "w": 0.3, "h": 0.3}
            x, y, w, h = cv2.boundingRect(points)
            height, width = diff.shape[:2]
            return {"x": x / width, "y": y / height, "w": w / width, "h": h / height}
        except Exception:
            return {"x": 0.35, "y": 0.35, "w": 0.3, "h": 0.3}
