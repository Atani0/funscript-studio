from __future__ import annotations

from typing import Dict, List, Tuple


def bbox_center(bbox: List[float]) -> Tuple[float, float]:
    return bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2


class MultiPersonTracker:
    def __init__(self) -> None:
        self.next_id = 1
        self.tracks: Dict[int, Dict[str, object]] = {}

    def update(self, time_ms: int, detections: List[Dict[str, object]]) -> Dict[str, object]:
        assigned: Dict[int, Dict[str, object]] = {}
        used_ids = set()
        for detection in detections:
            bbox = detection.get("bbox", [0.3, 0.2, 0.4, 0.6])
            center = bbox_center(bbox)  # type: ignore[arg-type]
            best_id = None
            best_distance = 999.0
            for track_id, track in self.tracks.items():
                if track_id in used_ids:
                    continue
                previous_center = track.get("center", center)
                distance = ((center[0] - previous_center[0]) ** 2 + (center[1] - previous_center[1]) ** 2) ** 0.5  # type: ignore[index]
                if distance < best_distance:
                    best_distance = distance
                    best_id = track_id
            if best_id is None or best_distance > 0.22:
                best_id = self.next_id
                self.next_id += 1
            used_ids.add(best_id)
            assigned[best_id] = {
                "track_id": best_id,
                "bbox": bbox,
                "center": [center[0], center[1]],
                "confidence": float(detection.get("confidence", 0.5)),
            }
        self.tracks = assigned
        return {"time": time_ms, "tracks": list(assigned.values())}
