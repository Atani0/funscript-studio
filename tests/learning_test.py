from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from learning.parameter_fitter import fit_parameters
from learning.perception_aligner import align_perception_to_script
from learning.script_feature_extractor import extract_script_features, load_actions
from learning.similarity_index import build_similarity_index, query
from learning.training_dataset import add_example, load_dataset


def fake_perception():
    return {
        "duration": 4000,
        "summary": {"style": "animation_3d"},
        "segments": [
            {
                "start": i * 250,
                "end": i * 250 + 250,
                "style": "animation_3d",
                "shot_type": "full_body",
                "visual": {"motion_intensity": 0.4 + (i % 3) * 0.1, "body_motion_overall": 0.5, "hand_motion": 0.2, "leg_motion": 0.4, "hip_motion": 0.6, "scene_change": i == 4},
                "audio": {"beat_strength": 0.8 if i % 2 == 0 else 0.2, "onset_strength": 0.5, "transient_strength": 0.2},
                "interaction": {"interaction_intensity": 0.1},
            }
            for i in range(16)
        ],
    }


def test_learning_pipeline():
    actions = [{"at": i * 260, "pos": 30 + ((i * 17) % 45)} for i in range(14)]
    features = extract_script_features(actions, 4000)
    assert features["action_count"] == 14
    samples = align_perception_to_script(fake_perception(), actions, [1000])
    assert samples and "features" in samples[0] and "target" in samples[0]
    with tempfile.TemporaryDirectory() as tmp:
        report = fit_parameters(samples, "unit_style", tmp)
        assert Path(report["profile_path"]).exists()
        index = build_similarity_index(samples, {"example": actions}, str(Path(tmp) / "similarity_index.json"))
        assert index["segments"]
        results = query(index, samples[0]["features"], 1)
        assert results and results[0]["similarity"] > 0.1


if __name__ == "__main__":
    test_learning_pipeline()
    print("PASS learning_test")

