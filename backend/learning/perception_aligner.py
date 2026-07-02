from __future__ import annotations

from typing import Dict, List

from .script_feature_extractor import extract_script_features


def _segments_in_window(perception: Dict[str, object], start: int, end: int) -> List[Dict[str, object]]:
    return [seg for seg in perception.get("segments", []) if int(seg.get("start", 0)) < end and int(seg.get("end", 0)) > start]


def _avg(items: List[float]) -> float:
    return sum(items) / max(1, len(items))


def perception_features(perception: Dict[str, object], start: int, end: int) -> Dict[str, object]:
    segs = _segments_in_window(perception, start, end)
    visual = [seg.get("visual", {}) for seg in segs]
    audio = [seg.get("audio", {}) for seg in segs]
    inter = [seg.get("interaction", {}) for seg in segs]
    return {
        "audio_beat_strength": _avg([float(a.get("beat_strength", 0.0)) for a in audio]),
        "audio_onset_strength": _avg([float(a.get("onset_strength", 0.0)) for a in audio]),
        "audio_transient_strength": _avg([float(a.get("transient_strength", 0.0)) for a in audio]),
        "visual_motion": _avg([float(v.get("motion_intensity", 0.0)) for v in visual]),
        "body_motion_overall": _avg([float(v.get("body_motion_overall", 0.0)) for v in visual]),
        "hand_motion": _avg([float(v.get("hand_motion", 0.0)) for v in visual]),
        "leg_motion": _avg([float(v.get("leg_motion", 0.0)) for v in visual]),
        "hip_motion": _avg([float(v.get("hip_motion", 0.0)) for v in visual]),
        "interaction_intensity": _avg([float(i.get("interaction_intensity", 0.0)) for i in inter]),
        "shot_type": max([str(seg.get("shot_type", "unknown")) for seg in segs], key=[str(seg.get("shot_type", "unknown")) for seg in segs].count) if segs else "unknown",
        "style": str(perception.get("summary", {}).get("style", perception.get("style", {}).get("style", "unknown"))),
        "scene_change_count": sum(1 for v in visual if v.get("scene_change")),
    }


def align_perception_to_script(perception: Dict[str, object], actions: List[Dict[str, int]], windows: List[int] | None = None) -> List[Dict[str, object]]:
    duration = int(perception.get("duration", actions[-1]["at"] if actions else 0))
    windows = windows or [1000, 2000, 4000]
    samples: List[Dict[str, object]] = []
    for window in windows:
        for start in range(0, max(duration, window), window):
            end = min(duration, start + window)
            window_actions = [action for action in actions if start <= action["at"] < end]
            stats = extract_script_features(window_actions, end - start)
            amp = stats.get("amplitude", {}) if isinstance(stats.get("amplitude"), dict) else {}
            samples.append({
                "start": start,
                "end": end,
                "window_ms": window,
                "features": perception_features(perception, start, end),
                "target": {
                    "density": stats.get("density", 0.0),
                    "amplitude_min": amp.get("min", 50),
                    "amplitude_max": amp.get("max", 50),
                    "avg_interval_ms": stats.get("avg_interval_ms", 0),
                    "smoothness": stats.get("style", {}).get("smoothness", 0.5) if isinstance(stats.get("style"), dict) else 0.5,
                    "beat_alignment": stats.get("style", {}).get("beat_matched", 0.0) if isinstance(stats.get("style"), dict) else 0.0,
                },
            })
    return samples

