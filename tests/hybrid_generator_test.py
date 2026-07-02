from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from generation.event_candidate_extractor import extract_event_candidates
from generation.motion_planner import plan_motion
from generation.action_synthesizer import synthesize_actions
from generation.quality_metrics import evaluate_actions
from learning.learned_profile import default_profile


def fake_perception():
    return {
        "duration": 5000,
        "segments": [
            {
                "start": i * 250,
                "end": i * 250 + 250,
                "shot_type": "full_body",
                "style": "animation_3d",
                "visual": {
                    "motion_intensity": 0.2 + (i % 5) * 0.13,
                    "body_motion_overall": 0.3 + (i % 4) * 0.12,
                    "hand_motion": 0.1 + (i % 2) * 0.2,
                    "leg_motion": 0.2 + (i % 3) * 0.18,
                    "hip_motion": 0.25 + (i % 4) * 0.15,
                    "scene_change": i == 8,
                },
                "interaction": {"interaction_intensity": 0.1},
            }
            for i in range(20)
        ],
    }


def test_hybrid_generator_primitives_are_not_fixed_22_78():
    profile = default_profile()
    events = [{"time": i * 310 + (i % 3) * 23, "type": "beat" if i % 2 == 0 else "onset", "strength": 0.55 + (i % 4) * 0.1} for i in range(14)]
    candidates = extract_event_candidates(events, fake_perception(), profile, "balanced")
    plan = plan_motion(candidates, fake_perception(), profile, None, "balanced")
    actions = synthesize_actions(plan, profile, 5000)
    assert len(actions) > 6
    assert len({action["pos"] for action in actions}) > 4
    metrics = evaluate_actions(actions, [int(event["time"]) for event in events if event["type"] == "beat"])
    assert metrics["fixed_peak_valley_score"] < 0.8


if __name__ == "__main__":
    test_hybrid_generator_primitives_are_not_fixed_22_78()
    print("PASS hybrid_generator_test")
