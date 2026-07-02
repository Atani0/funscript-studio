from __future__ import annotations

from typing import Dict, List

from .multi_person_tracker import bbox_center
from .perception_schema import clamp01


class InteractionAnalyzer:
    def __init__(self) -> None:
        self.previous_centers: Dict[int, List[float]] = {}
        self.previous_motion: Dict[int, float] = {}

    def analyze(self, time_ms: int, tracks_frame: Dict[str, object], pose_frame: Dict[str, object]) -> Dict[str, object]:
        tracks = tracks_frame.get("tracks", [])
        person_count = len(tracks)
        if person_count < 2:
            self._remember(tracks, pose_frame)
            return {"time": time_ms, "interaction": {
                "person_count": person_count,
                "proximity": 0.0,
                "approach_speed": 0.0,
                "sync_motion": 0.0,
                "hand_contact_likelihood": 0.0,
                "body_contact_likelihood": 0.0,
                "interaction_intensity": 0.0,
            }}

        centers = [track.get("center", bbox_center(track.get("bbox", [0, 0, 0, 0]))) for track in tracks]  # type: ignore[arg-type]
        min_distance = min(
            ((centers[i][0] - centers[j][0]) ** 2 + (centers[i][1] - centers[j][1]) ** 2) ** 0.5
            for i in range(len(centers))
            for j in range(i + 1, len(centers))
        )
        proximity = clamp01(1.0 - min_distance / 0.7)
        approach = 0.0
        motions: List[float] = []
        for track in tracks:
            track_id = int(track.get("track_id", 0))
            center = track.get("center", [0.5, 0.5])
            previous = self.previous_centers.get(track_id)
            if previous:
                motions.append(clamp01(((center[0] - previous[0]) ** 2 + (center[1] - previous[1]) ** 2) ** 0.5 * 12))  # type: ignore[index]
        if len(motions) >= 2:
            avg = sum(motions) / len(motions)
            spread = sum(abs(item - avg) for item in motions) / len(motions)
            sync = clamp01(1.0 - spread / max(avg, 0.05))
        else:
            sync = 0.0
        if self.previous_centers:
            approach = clamp01(proximity * (sum(motions) / max(1, len(motions))) * 1.2)
        hand_contact = clamp01(proximity * 0.65 + sync * 0.25)
        body_contact = clamp01(proximity * 0.8)
        intensity = clamp01(0.38 * proximity + 0.24 * approach + 0.24 * sync + 0.14 * max(hand_contact, body_contact))
        self._remember(tracks, pose_frame)
        return {"time": time_ms, "interaction": {
            "person_count": person_count,
            "proximity": proximity,
            "approach_speed": approach,
            "sync_motion": sync,
            "hand_contact_likelihood": hand_contact,
            "body_contact_likelihood": body_contact,
            "interaction_intensity": intensity,
        }}

    def _remember(self, tracks: List[Dict[str, object]], pose_frame: Dict[str, object]) -> None:
        self.previous_centers = {int(track.get("track_id", 0)): track.get("center", [0.5, 0.5]) for track in tracks}  # type: ignore[assignment]
