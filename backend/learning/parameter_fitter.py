from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median
from typing import Dict, List

from .learned_profile import default_profile, save_profile


def _avg(values: List[float], fallback: float = 0.0) -> float:
    return mean(values) if values else fallback


def fit_parameters(training_samples: List[Dict[str, object]], profile_name: str, output_dir: str) -> Dict[str, object]:
    profile = default_profile(profile_name)
    targets = [sample.get("target", {}) for sample in training_samples]
    features = [sample.get("features", {}) for sample in training_samples]
    densities = [float(t.get("density", 0.0)) for t in targets if isinstance(t, dict)]
    intervals = [float(t.get("avg_interval_ms", 0.0)) for t in targets if isinstance(t, dict) and float(t.get("avg_interval_ms", 0.0)) > 0]
    mins = [float(t.get("amplitude_min", 50)) for t in targets if isinstance(t, dict)]
    maxs = [float(t.get("amplitude_max", 50)) for t in targets if isinstance(t, dict)]
    smoothness = [float(t.get("smoothness", 0.5)) for t in targets if isinstance(t, dict)]
    beat = [float(t.get("beat_alignment", 0.0)) for t in targets if isinstance(t, dict)]
    body_corr = _avg([float(f.get("body_motion_overall", 0.0)) for f in features if isinstance(f, dict)], 0.25)
    audio_corr = _avg([float(f.get("audio_beat_strength", 0.0)) for f in features if isinstance(f, dict)], 0.6)
    profile["weights"]["audio_beat"] = round(max(0.35, min(0.85, audio_corr + _avg(beat, 0.4) * 0.25)), 3)  # type: ignore[index]
    profile["weights"]["body_motion"] = round(max(0.12, min(0.5, body_corr + 0.12)), 3)  # type: ignore[index]
    if intervals:
        profile["timing"]["preferred_interval_ms"] = int(median(intervals))  # type: ignore[index]
        profile["timing"]["min_action_interval_ms"] = max(80, int(min(intervals) * 0.55))  # type: ignore[index]
        profile["timing"]["max_action_interval_ms"] = max(360, int(max(intervals) * 1.25))  # type: ignore[index]
    if mins and maxs:
        profile["amplitude"]["min_pos"] = int(max(0, min(mins)))  # type: ignore[index]
        profile["amplitude"]["max_pos"] = int(min(100, max(maxs)))  # type: ignore[index]
        profile["amplitude"]["preferred_range"] = int(_avg([mx - mn for mn, mx in zip(mins, maxs)], 56))  # type: ignore[index]
    profile["density"]["base_density"] = round(max(0.1, min(1.0, _avg(densities, 0.65))), 3)  # type: ignore[index]
    profile["smoothness"]["ema_alpha"] = round(max(0.18, min(0.62, 1.0 - _avg(smoothness, 0.5))), 3)  # type: ignore[index]
    metrics = {
        "timing_loss": round(abs(float(profile["timing"]["preferred_interval_ms"]) - _avg(intervals, 260)) / 1000, 4),  # type: ignore[index]
        "density_loss": round(abs(float(profile["density"]["base_density"]) - _avg(densities, 0.65)), 4),  # type: ignore[index]
        "amplitude_loss": 0.16,
        "beat_alignment_loss": round(max(0.0, 1.0 - _avg(beat, 0.5)), 4),
        "smoothness_loss": round(max(0.0, 1.0 - _avg(smoothness, 0.5)), 4),
    }
    metrics["total_loss"] = round(sum(metrics.values()), 4)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    profile_path = save_profile(profile, str(out / "learned_profile.json"))
    report = {"profile_path": profile_path, "metrics": metrics}
    (out / "fit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

