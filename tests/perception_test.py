from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from perception.audio_analyzer import AudioAnalyzer
from perception.feature_fusion import fuse_features
from perception.frame_sampler import FrameSample
from perception.perception_schema import load_json, save_json
from perception.pose_analyzer import PoseAnalyzer
from perception.visual_analyzer import VisualAnalyzer


def test_pose_analyzer_fallback_outputs_motion():
    sample = FrameSample(
        frame_index=0,
        timestamp_ms=100,
        image=None,
        original_fps=30.0,
        analysis_fps=10.0,
        width=1280,
        height=720,
    )
    analyzer = PoseAnalyzer(backend="optical_flow_fallback")
    result = analyzer.analyze(sample, visual={
        "motion": 0.42,
        "motion_region": {"x": 0.35, "y": 0.45, "w": 0.22, "h": 0.2},
    })
    assert result["backend"] == "optical_flow_fallback"
    assert result["persons"]
    assert 0 <= result["body_motion"]["overall"] <= 1


def test_visual_analyzer_handles_missing_frame():
    sample = FrameSample(
        frame_index=0,
        timestamp_ms=0,
        image=None,
        original_fps=30.0,
        analysis_fps=10.0,
        width=1280,
        height=720,
    )
    result = VisualAnalyzer().analyze(sample)
    assert result["motion"] == 0.0
    assert result["main_motion_region"]["w"] > 0


def test_fusion_schema_and_json_roundtrip():
    perception = fuse_features(
        duration_ms=1000,
        style={"style": "unknown", "confidence": 0.5, "reason": "unit test"},
        visual_frames=[{"time": 0, "motion": 0.2, "scene_change": False}],
        pose_frames=[{"time": 0, "body_motion": {"overall": 0.3, "upper_body": 0.1, "lower_body": 0.2, "hands": 0.1, "legs": 0.2, "hips": 0.3, "torso": 0.2}, "confidence": 0.6}],
        shot_frames=[{"time": 0, "shot_type": "unknown", "confidence": 0.5}],
        interaction_frames=[{"time": 0, "interaction": {"person_count": 1, "interaction_intensity": 0.0, "proximity": 0.0, "sync_motion": 0.0, "hand_contact_likelihood": 0.0, "body_contact_likelihood": 0.0}}],
        audio_result={"mode": "event", "samples": [{"time": 0, "audio": {"beat_strength": 0.0, "onset": 0.4, "tempo_confidence": 0.0}, "audio_event": {"transient_strength": 0.5, "clap_likelihood": 0.2}}]},
    )
    assert perception["segments"]
    segment = perception["segments"][0]
    assert "visual" in segment
    assert "audio" in segment
    assert "suggested_motion" in segment

    with tempfile.TemporaryDirectory() as tmp:
        path = save_json(perception, tmp, prefix="perception_test")
        loaded = load_json(path)
        assert loaded["segments"][0]["suggested_motion"]["intensity"] == segment["suggested_motion"]["intensity"]


def test_audio_analyzer_outputs_events_when_ffmpeg_available():
    ffmpeg = os.environ.get("FFMPEG_PATH", "ffmpeg")
    try:
        subprocess.run([ffmpeg, "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("ffmpeg not available; skipping synthetic audio integration test")
        return

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "tone.wav"
        subprocess.run([
            ffmpeg,
            "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=880:duration=1",
            "-af", "volume=0.8",
            str(wav),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        result = AudioAnalyzer().analyze(str(wav), ffmpeg, duration_ms=1000, mode="auto", step_ms=100)
        assert result["samples"]
        assert result["mode"] in {"music", "event", "mixed", "unknown"}


if __name__ == "__main__":
    tests = [
        test_pose_analyzer_fallback_outputs_motion,
        test_visual_analyzer_handles_missing_frame,
        test_fusion_schema_and_json_roundtrip,
        test_audio_analyzer_outputs_events_when_ffmpeg_available,
    ]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failures.append((test.__name__, exc))
            print(f"FAIL {test.__name__}: {exc}")
    if failures:
        print(json.dumps([name for name, _ in failures], ensure_ascii=False))
        raise SystemExit(1)
