from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def default_profile(profile_name: str = "default_hybrid") -> Dict[str, object]:
    return {
        "profile_name": profile_name,
        "version": "1.0",
        "weights": {
            "audio_beat": 0.60,
            "audio_onset": 0.22,
            "audio_transient": 0.12,
            "visual_motion": 0.20,
            "body_motion": 0.28,
            "hand_motion": 0.08,
            "leg_motion": 0.12,
            "hip_motion": 0.18,
            "interaction": 0.08,
            "scene_change": 0.05,
        },
        "timing": {
            "min_action_interval_ms": 120,
            "preferred_interval_ms": 260,
            "max_action_interval_ms": 650,
            "beat_snap_tolerance_ms": 90,
        },
        "amplitude": {
            "min_pos": 12,
            "max_pos": 88,
            "center_pos": 50,
            "min_range": 18,
            "preferred_range": 56,
            "max_range": 76,
            "variance": 0.35,
        },
        "density": {
            "base_density": 0.65,
            "low_motion_density": 0.35,
            "high_motion_density": 0.85,
        },
        "smoothness": {
            "ema_alpha": 0.35,
            "preserve_peaks": True,
            "avoid_mechanical_repetition": True,
        },
        "style_bias": {
            "beat_matched": 0.8,
            "energetic": 0.7,
            "pose_aware": 0.6,
            "interaction_aware": 0.4,
        },
    }


def load_profile(path: str | None) -> Dict[str, object]:
    if not path:
        return default_profile()
    file = Path(path)
    if not file.exists():
        return default_profile()
    return json.loads(file.read_text(encoding="utf-8"))


def save_profile(profile: Dict[str, object], path: str) -> str:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(file)

