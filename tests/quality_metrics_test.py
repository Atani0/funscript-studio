from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from generation.quality_metrics import evaluate_actions


def test_quality_metrics_detects_fixed_peak_valley():
    actions = [{"at": i * 250, "pos": 22 if i % 2 == 0 else 78} for i in range(24)]
    metrics = evaluate_actions(actions)
    assert metrics["mechanical_repetition_score"] > 0.1
    assert metrics["fixed_peak_valley_score"] > 0.4
    assert metrics["warnings"]


if __name__ == "__main__":
    test_quality_metrics_detects_fixed_peak_valley()
    print("PASS quality_metrics_test")

