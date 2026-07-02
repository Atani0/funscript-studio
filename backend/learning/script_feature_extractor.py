from __future__ import annotations

import json
from statistics import mean, median
from typing import Dict, List

from generation.quality_metrics import evaluate_actions


def load_actions(path: str) -> List[Dict[str, int]]:
    data = json.loads(open(path, "r", encoding="utf-8").read())
    actions = []
    for item in data.get("actions", []):
        try:
            actions.append({"at": max(0, int(round(float(item["at"])))), "pos": max(0, min(100, int(round(float(item["pos"])))) )})
        except Exception:
            continue
    return sorted(actions, key=lambda action: action["at"])


def extract_script_features(actions: List[Dict[str, int]], duration_ms: int | None = None, beat_times: List[int] | None = None) -> Dict[str, object]:
    if not actions:
        return {"duration_ms": duration_ms or 0, "action_count": 0, "style": {}}
    duration = duration_ms or max(action["at"] for action in actions)
    intervals = [actions[i]["at"] - actions[i - 1]["at"] for i in range(1, len(actions))]
    positions = [action["pos"] for action in actions]
    speeds = [abs(positions[i] - positions[i - 1]) / max(1, intervals[i - 1]) * 250 for i in range(1, len(positions))] if intervals else []
    direction_changes = 0
    for i in range(2, len(positions)):
        if (positions[i] - positions[i - 1]) * (positions[i - 1] - positions[i - 2]) < 0:
            direction_changes += 1
    metrics = evaluate_actions(actions, beat_times)
    low_sections = sum(1 for delta in speeds if delta < 4) if speeds else 0
    high_sections = sum(1 for delta in speeds if delta > 24) if speeds else 0
    return {
        "duration_ms": duration,
        "action_count": len(actions),
        "action_times": [action["at"] for action in actions],
        "action_intervals": intervals,
        "avg_interval_ms": round(mean(intervals), 2) if intervals else 0,
        "median_interval_ms": round(median(intervals), 2) if intervals else 0,
        "density": round(len(actions) / max(1, duration / 1000) / 3.0, 4),
        "amplitude": {
            "min": min(positions),
            "max": max(positions),
            "center": round(mean(positions), 2),
            "mean_range": max(positions) - min(positions),
            "variance": metrics["amplitude_variance"],
        },
        "speed": {
            "mean": round(mean(speeds), 4) if speeds else 0.0,
            "p90": round(sorted(speeds)[int(len(speeds) * 0.9)] if speeds else 0.0, 4),
        },
        "direction_change_rate": round(direction_changes / max(1, len(actions) - 2), 4),
        "pause_sections": low_sections,
        "high_intensity_sections": high_sections,
        "style": {
            "beat_matched": metrics["beat_alignment_rate"],
            "smoothness": metrics["smoothness"],
            "intensity": round(mean(speeds) / 40, 4) if speeds else 0.0,
            "repetition": metrics["mechanical_repetition_score"],
        },
    }

