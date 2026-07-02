from __future__ import annotations

from typing import Dict, List

from .perception_schema import clamp01


class ShotAnalyzer:
    def analyze(self, time_ms: int, pose: Dict[str, object], visual: Dict[str, object]) -> Dict[str, object]:
        persons = pose.get("persons", [])
        region = visual.get("main_motion_region", {"x": 0.35, "y": 0.35, "w": 0.3, "h": 0.3})
        if not persons:
            area = float(region.get("w", 0.3)) * float(region.get("h", 0.3))  # type: ignore[union-attr]
            shot_type = "wide_scene" if area < 0.12 else "unknown"
            return {"time": time_ms, "shot_type": shot_type, "confidence": 0.35, "main_motion_region": region}

        person = persons[0]  # type: ignore[index]
        bbox = person.get("bbox", [0.25, 0.2, 0.5, 0.6])
        area = float(bbox[2]) * float(bbox[3])
        y = float(bbox[1])
        h = float(bbox[3])
        keypoints = person.get("keypoints", {})
        visible_count = sum(1 for point in keypoints.values() if point[2] > 0.3) if isinstance(keypoints, dict) else 0

        if area > 0.55 and y < 0.12:
            shot = "face_closeup" if visible_count < 6 else "torso_closeup"
        elif area > 0.38 and h < 0.55:
            shot = "torso_closeup"
        elif y > 0.35:
            shot = "lower_body"
        elif visible_count >= 10 and area > 0.18:
            shot = "full_body"
        elif visible_count >= 5:
            shot = "upper_body"
        elif area < 0.12:
            shot = "wide_scene"
        else:
            shot = "unknown"

        return {"time": time_ms, "shot_type": shot, "confidence": clamp01(0.45 + visible_count / 24 + area * 0.25), "main_motion_region": region}
