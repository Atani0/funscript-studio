from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List


def clamp01(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "+"):
            return default
        parsed = float(value)
        if parsed != parsed or parsed in (float("inf"), float("-inf")):
            return default
        return parsed
    except Exception:
        return default


def normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high <= low:
        return [0.0 for _ in values]
    return [clamp01((value - low) / (high - low)) for value in values]


def smooth(values: List[float], alpha: float = 0.35) -> List[float]:
    if not values:
        return []
    output: List[float] = []
    ema = values[0]
    for value in values:
        ema = alpha * value + (1.0 - alpha) * ema
        output.append(clamp01(ema))
    return output


def empty_segment(start: int, end: int) -> Dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "style": "unknown",
        "shot_type": "unknown",
        "confidence": 0.0,
        "visual": {
            "motion_intensity": 0.0,
            "body_motion_overall": 0.0,
            "upper_body_motion": 0.0,
            "lower_body_motion": 0.0,
            "hand_motion": 0.0,
            "leg_motion": 0.0,
            "hip_motion": 0.0,
            "torso_motion": 0.0,
            "scene_change": False,
        },
        "interaction": {
            "person_count": 0,
            "interaction_intensity": 0.0,
            "proximity": 0.0,
            "sync_motion": 0.0,
            "contact_likelihood": 0.0,
        },
        "audio": {
            "mode": "unknown",
            "beat_strength": 0.0,
            "onset_strength": 0.0,
            "transient_strength": 0.0,
            "clap_likelihood": 0.0,
            "tempo_confidence": 0.0,
        },
        "suggested_motion": {
            "intensity": 0.0,
            "rhythm_density": 0.0,
            "smoothness": 0.5,
            "accent": 0.0,
        },
        "explain": [],
    }


def save_json(data: Dict[str, Any], directory: str | Path, prefix: str = "perception") -> str:
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{prefix}_{int(time.time() * 1000)}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
