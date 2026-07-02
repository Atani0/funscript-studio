from __future__ import annotations

from statistics import mean, median
from typing import Dict, List


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    spread = max(values) - min(values) or 1.0
    return min(1.0, mean([(value - avg) ** 2 for value in values]) ** 0.5 / spread)


def evaluate_actions(actions: List[Dict[str, int]], beat_times: List[int] | None = None) -> Dict[str, object]:
    if not actions:
        return {
            "action_count": 0,
            "avg_interval_ms": 0,
            "interval_variance": 0.0,
            "amplitude_variance": 0.0,
            "beat_alignment_rate": 0.0,
            "mechanical_repetition_score": 1.0,
            "fixed_peak_valley_score": 1.0,
            "smoothness": 0.0,
            "warnings": ["no actions generated"],
        }
    ordered = sorted(actions, key=lambda item: int(item["at"]))
    intervals = [int(ordered[i]["at"]) - int(ordered[i - 1]["at"]) for i in range(1, len(ordered))]
    positions = [int(item["pos"]) for item in ordered]
    deltas = [abs(positions[i] - positions[i - 1]) for i in range(1, len(positions))]
    unique_positions = len(set(positions))
    pair_keys = [f"{positions[i-1]}:{positions[i]}" for i in range(1, len(positions))]
    most_common_pair = max((pair_keys.count(key) for key in set(pair_keys)), default=0)
    mechanical = most_common_pair / max(1, len(pair_keys))
    fixed_peak_valley = 1.0 - min(1.0, unique_positions / max(6, min(24, len(positions))))
    beat_times = beat_times or []
    aligned = 0
    if beat_times:
        for action in ordered:
            if min((abs(int(action["at"]) - beat) for beat in beat_times), default=999999) <= 95:
                aligned += 1
    beat_alignment = aligned / max(1, len(ordered)) if beat_times else 0.0
    smoothness = 1.0 - min(1.0, _variance(deltas) + (mean(deltas) / 100 if deltas else 0.0) * 0.15)
    warnings = []
    if mechanical > 0.42:
        warnings.append("mechanical repetition is high")
    if fixed_peak_valley > 0.45:
        warnings.append("peak/valley positions are too fixed")
    if intervals and _variance([float(item) for item in intervals]) < 0.08:
        warnings.append("action intervals are too uniform")
    return {
        "action_count": len(ordered),
        "avg_interval_ms": round(mean(intervals), 2) if intervals else 0,
        "median_interval_ms": round(median(intervals), 2) if intervals else 0,
        "interval_variance": round(_variance([float(item) for item in intervals]), 4),
        "amplitude_variance": round(_variance([float(pos) for pos in positions]), 4),
        "beat_alignment_rate": round(beat_alignment, 4),
        "mechanical_repetition_score": round(mechanical, 4),
        "fixed_peak_valley_score": round(fixed_peak_valley, 4),
        "smoothness": round(max(0.0, min(1.0, smoothness)), 4),
        "warnings": warnings,
    }

