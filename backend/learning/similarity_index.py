from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional


FEATURE_KEYS = [
    "audio_beat_strength", "audio_onset_strength", "audio_transient_strength",
    "visual_motion", "body_motion_overall", "hand_motion", "leg_motion", "hip_motion",
    "interaction_intensity", "scene_change_count",
]


def vectorize(features: Dict[str, object]) -> List[float]:
    raw = [float(features.get(key, 0.0)) for key in FEATURE_KEYS]
    norm = math.sqrt(sum(value * value for value in raw)) or 1.0
    return [value / norm for value in raw]


def cosine(a: List[float], b: List[float]) -> float:
    size = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(size))


def build_similarity_index(aligned_samples: List[Dict[str, object]], actions_by_example: Dict[str, List[Dict[str, int]]], output_path: str) -> Dict[str, object]:
    segments = []
    for index, sample in enumerate(aligned_samples):
        features = sample.get("features", {})
        target = sample.get("target", {})
        start = int(sample.get("start", 0))
        end = int(sample.get("end", start))
        example_id = str(sample.get("example_id", "example"))
        actions = actions_by_example.get(example_id, [])
        rel = [{"at": action["at"] - start, "pos": action["pos"]} for action in actions if start <= action["at"] < end]
        if isinstance(features, dict):
            segments.append({
                "example_id": example_id,
                "segment_id": f"{example_id}_{start}_{end}_{index}",
                "start": start,
                "end": end,
                "feature_vector": vectorize(features),
                "features": features,
                "script_stats": target,
                "actions_relative": rel,
            })
    data = {"version": "1.0", "segments": segments}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def load_index(path: str | None) -> Dict[str, object]:
    if not path or not Path(path).exists():
        return {"segments": []}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def query(index: Dict[str, object], features: Dict[str, object], top_k: int = 3, shot_type: Optional[str] = None, style: Optional[str] = None) -> List[Dict[str, object]]:
    vec = vectorize(features)
    results = []
    for seg in index.get("segments", []):
        seg_features = seg.get("features", {})
        if shot_type and isinstance(seg_features, dict) and seg_features.get("shot_type") != shot_type:
            continue
        if style and isinstance(seg_features, dict) and seg_features.get("style") != style:
            continue
        scored = dict(seg)
        scored["similarity"] = cosine(vec, seg.get("feature_vector", []))
        results.append(scored)
    return sorted(results, key=lambda item: float(item.get("similarity", 0.0)), reverse=True)[:top_k]

