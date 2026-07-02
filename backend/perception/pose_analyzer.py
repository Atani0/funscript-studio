from __future__ import annotations

from typing import Dict, List, Optional

from .frame_sampler import FrameSample
from .perception_schema import clamp01


KEYPOINTS = [
    "nose",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


class PoseAnalyzer:
    def __init__(self, backend: str = "mediapipe_pose") -> None:
        self.backend_name = backend
        self.pose = None
        self.previous_keypoints: Optional[Dict[str, List[float]]] = None
        self._init_backend()

    def _init_backend(self) -> None:
        if self.backend_name != "mediapipe_pose":
            return
        try:
            import mediapipe as mp  # type: ignore
            self.pose = mp.solutions.pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False)
        except Exception:
            self.pose = None
            self.backend_name = "optical_flow_fallback"

    def analyze(self, sample: FrameSample, visual: Dict[str, object]) -> Dict[str, object]:
        if self.pose is not None:
            result = self._mediapipe(sample)
            if result["persons"]:
                return result
        return self._fallback(sample, visual)

    def _mediapipe(self, sample: FrameSample) -> Dict[str, object]:
        try:
            import cv2  # type: ignore
            image = cv2.cvtColor(sample.image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image)
            if not results.pose_landmarks:
                return {"time": sample.timestamp_ms, "persons": [], "backend": self.backend_name, "confidence": 0.0}
            landmarks = results.pose_landmarks.landmark
            mp_index = {
                "nose": 0,
                "left_shoulder": 11,
                "right_shoulder": 12,
                "left_elbow": 13,
                "right_elbow": 14,
                "left_wrist": 15,
                "right_wrist": 16,
                "left_hip": 23,
                "right_hip": 24,
                "left_knee": 25,
                "right_knee": 26,
                "left_ankle": 27,
                "right_ankle": 28,
            }
            keypoints = {name: [clamp01(landmarks[idx].x), clamp01(landmarks[idx].y), clamp01(landmarks[idx].visibility)] for name, idx in mp_index.items()}
            visible = [point for point in keypoints.values() if point[2] > 0.35]
            if not visible:
                return {"time": sample.timestamp_ms, "persons": [], "backend": self.backend_name, "confidence": 0.0}
            xs = [point[0] for point in visible]
            ys = [point[1] for point in visible]
            bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            confidence = sum(point[2] for point in visible) / len(visible)
            dynamics = self._dynamics(keypoints)
            self.previous_keypoints = keypoints
            return {
                "time": sample.timestamp_ms,
                "backend": self.backend_name,
                "confidence": confidence,
                "persons": [{"track_id": 0, "bbox": bbox, "pose_confidence": confidence, "keypoints": keypoints}],
                "body_motion": dynamics["body_motion"],
                "body_dynamics": dynamics["body_dynamics"],
            }
        except Exception:
            return {"time": sample.timestamp_ms, "persons": [], "backend": "optical_flow_fallback", "confidence": 0.0}

    def _fallback(self, sample: FrameSample, visual: Dict[str, object]) -> Dict[str, object]:
        region = visual.get("main_motion_region", {"x": 0.35, "y": 0.25, "w": 0.3, "h": 0.5})
        motion = clamp01(float(visual.get("motion", 0.0)))
        bbox = [region["x"], region["y"], max(0.12, region["w"]), max(0.12, region["h"])]  # type: ignore[index]
        cx = bbox[0] + bbox[2] / 2
        cy = bbox[1] + bbox[3] / 2
        keypoints = {
            "nose": [cx, max(0.02, bbox[1]), 0.18],
            "left_shoulder": [bbox[0], cy - bbox[3] * 0.18, 0.2],
            "right_shoulder": [bbox[0] + bbox[2], cy - bbox[3] * 0.18, 0.2],
            "left_elbow": [bbox[0], cy, 0.15],
            "right_elbow": [bbox[0] + bbox[2], cy, 0.15],
            "left_wrist": [bbox[0], cy + bbox[3] * 0.1, 0.12],
            "right_wrist": [bbox[0] + bbox[2], cy + bbox[3] * 0.1, 0.12],
            "left_hip": [bbox[0] + bbox[2] * 0.25, cy + bbox[3] * 0.2, 0.2],
            "right_hip": [bbox[0] + bbox[2] * 0.75, cy + bbox[3] * 0.2, 0.2],
            "left_knee": [bbox[0] + bbox[2] * 0.25, bbox[1] + bbox[3] * 0.75, 0.12],
            "right_knee": [bbox[0] + bbox[2] * 0.75, bbox[1] + bbox[3] * 0.75, 0.12],
            "left_ankle": [bbox[0] + bbox[2] * 0.25, bbox[1] + bbox[3], 0.1],
            "right_ankle": [bbox[0] + bbox[2] * 0.75, bbox[1] + bbox[3], 0.1],
        }
        return {
            "time": sample.timestamp_ms,
            "backend": "optical_flow_fallback",
            "confidence": 0.2 if motion > 0 else 0.0,
            "persons": [{"track_id": 0, "bbox": bbox, "pose_confidence": 0.2, "keypoints": keypoints}] if motion > 0.03 else [],
            "body_motion": {
                "overall": motion,
                "upper_body": motion * 0.75,
                "lower_body": motion * 0.65,
                "hands": motion * 0.8,
                "legs": motion * 0.55,
                "hips": motion * 0.65,
                "torso": motion * 0.7,
            },
            "body_dynamics": {
                "center_velocity": motion,
                "vertical_bounce": motion * (0.8 if region.get("y", 0.5) > 0.35 else 0.45),  # type: ignore[union-attr]
                "horizontal_sway": motion * 0.7,
                "rotation_hint": motion * 0.35,
                "limb_extension": motion * 0.5,
                "pose_change_rate": motion,
            },
        }

    def _dynamics(self, keypoints: Dict[str, List[float]]) -> Dict[str, object]:
        if not self.previous_keypoints:
            overall = 0.0
            upper = lower = hands = legs = hips = torso = 0.0
        else:
            speeds = {}
            for name, point in keypoints.items():
                prev = self.previous_keypoints.get(name, point)
                speeds[name] = clamp01(((point[0] - prev[0]) ** 2 + (point[1] - prev[1]) ** 2) ** 0.5 * 12)
            hands = (speeds.get("left_wrist", 0) + speeds.get("right_wrist", 0)) / 2
            legs = (speeds.get("left_ankle", 0) + speeds.get("right_ankle", 0) + speeds.get("left_knee", 0) + speeds.get("right_knee", 0)) / 4
            hips = (speeds.get("left_hip", 0) + speeds.get("right_hip", 0)) / 2
            torso = (speeds.get("left_shoulder", 0) + speeds.get("right_shoulder", 0) + hips) / 3
            upper = (hands + torso) / 2
            lower = (legs + hips) / 2
            overall = sum(speeds.values()) / max(1, len(speeds))
        return {
            "body_motion": {
                "overall": clamp01(overall),
                "upper_body": clamp01(upper),
                "lower_body": clamp01(lower),
                "hands": clamp01(hands),
                "legs": clamp01(legs),
                "hips": clamp01(hips),
                "torso": clamp01(torso),
            },
            "body_dynamics": {
                "center_velocity": clamp01(overall),
                "vertical_bounce": clamp01(hips * 1.2),
                "horizontal_sway": clamp01(torso * 1.1),
                "rotation_hint": clamp01(abs(keypoints["left_shoulder"][0] - keypoints["right_shoulder"][0]) * torso),
                "limb_extension": clamp01((hands + legs) / 2),
                "pose_change_rate": clamp01(overall),
            },
        }
