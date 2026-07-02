from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from audio_analysis import analyze_audio
from generator import generate as fast_generate
from generation.action_synthesizer import synthesize_actions
from generation.event_candidate_extractor import extract_event_candidates
from generation.motion_planner import plan_motion
from generation.quality_metrics import evaluate_actions
from learning.learned_profile import load_profile
from learning.similarity_index import load_index, query
from perception.perception_engine import analyze_perception, load_perception


def _intensify_actions(actions: List[Dict[str, int]], rounds: int = 2, factor: float = 1.28) -> List[Dict[str, int]]:
    """Match the frontend “加剧当前轴” operation multiple times.

    Energetic hybrid mode should not merely add more candidate points; it should
    also widen the generated movement range. Keeping the same formula here makes
    backend generation consistent with pressing the UI intensify button.
    """
    amplified = [dict(action) for action in actions]
    for _ in range(max(0, rounds)):
        for action in amplified:
            pos = int(action.get("pos", 50))
            action["pos"] = max(0, min(100, round(50 + (pos - 50) * factor)))
    return amplified


def _segment_features_at(perception: Dict[str, object], time_ms: int) -> Dict[str, object]:
    segments = perception.get("segments", [])
    if not segments:
        return {}
    seg = min(segments, key=lambda item: abs(int(item.get("start", 0)) - time_ms))
    visual = seg.get("visual", {})
    audio = seg.get("audio", {})
    interaction = seg.get("interaction", {})
    return {
        "audio_beat_strength": audio.get("beat_strength", 0.0),
        "audio_onset_strength": audio.get("onset_strength", 0.0),
        "audio_transient_strength": audio.get("transient_strength", 0.0),
        "visual_motion": visual.get("motion_intensity", 0.0),
        "body_motion_overall": visual.get("body_motion_overall", 0.0),
        "hand_motion": visual.get("hand_motion", 0.0),
        "leg_motion": visual.get("leg_motion", 0.0),
        "hip_motion": visual.get("hip_motion", 0.0),
        "interaction_intensity": interaction.get("interaction_intensity", 0.0),
        "shot_type": seg.get("shot_type", "unknown"),
        "style": seg.get("style", "unknown"),
        "scene_change_count": 1 if visual.get("scene_change") else 0,
    }


def hybrid_generate(
    video_path: str,
    ffmpeg_path: str,
    perception_path: str = "",
    profile_path: str = "",
    dataset_name: str = "",
    mode: str = "hybrid",
    style: str = "balanced",
    axis: str = "stroke",
) -> Dict[str, object]:
    try:
        profile = load_profile(profile_path)
        if perception_path and Path(perception_path).exists():
            perception = load_perception(perception_path)
        else:
            out_dir = str(Path(__file__).resolve().parents[1] / "perception_outputs")
            perception = analyze_perception(video_path, ffmpeg_path, output_dir=out_dir)
            perception_path = str(perception.get("perceptionPath", ""))
        duration = int(perception.get("duration", 0))
        audio = analyze_audio(video_path, ffmpeg_path, duration)
        audio_events = audio.get("events", [])
        audio_energy = audio.get("energy", [])
        candidates = extract_event_candidates(
            audio_events,
            perception,
            profile,
            style,
            audio_energy if isinstance(audio_energy, list) else [],
            duration,
        )
        similar_used = False
        similar_matches: List[Dict[str, object]] = []
        index_path = ""
        if dataset_name:
            index_path = str(Path(__file__).resolve().parents[2] / "data" / "training_datasets" / dataset_name / "similarity_index.json")
        index = load_index(index_path)
        if mode == "learned_hybrid" and index.get("segments"):
            similar_used = True
            for event in candidates[:24]:
                similar_matches.extend(query(index, _segment_features_at(perception, int(event["time"])), 1))
        plan = plan_motion(candidates, perception, profile, similar_matches[:3], style)
        actions = synthesize_actions(plan, profile, duration)
        if style == "energetic":
            actions = _intensify_actions(actions, rounds=1)
        if mode == "hybrid_plus2":
            actions = _intensify_actions(actions, rounds=2)
        beat_times = [int(event["time"]) for event in audio_events if event.get("type") == "beat"]
        metrics = evaluate_actions(actions, beat_times)
        result = {
            "version": "1.0",
            "inverted": False,
            "range": 100,
            "actions": actions,
            "meta": {
                "engine": "hybrid-learned-generator" if mode == "learned_hybrid" else "hybrid-generator",
                "axis": axis,
                "style": style,
                "candidateEvents": len(candidates),
                "usedLearnedProfile": bool(profile_path and Path(profile_path).exists()),
                "usedSimilarSegments": similar_used,
                "quality": metrics,
                "similarSegments": similar_matches[:5],
                "perceptionPath": perception_path,
            },
        }
        return result
    except Exception as exc:
        duration = 0
        try:
            if perception_path and Path(perception_path).exists():
                duration = int(load_perception(perception_path).get("duration", 0))
        except Exception:
            duration = 0
        fallback = fast_generate(video_path, ffmpeg_path, duration or 120000)
        fallback.setdefault("meta", {})["engine"] = "hybrid-fallback-fast"
        fallback["meta"]["fallbackReason"] = str(exc)
        return fallback


def hybrid_generate_response(**kwargs) -> Dict[str, object]:
    result = hybrid_generate(**kwargs)
    actions = result.get("actions", [])
    quality = result.get("meta", {}).get("quality", {}) if isinstance(result.get("meta"), dict) else {}
    return {
        "ok": True,
        "funscript": result,
        "summary": {
            "actionCount": len(actions),
            "avgIntervalMs": quality.get("avg_interval_ms", 0),
            "amplitudeVariance": quality.get("amplitude_variance", 0),
            "beatAlignmentRate": quality.get("beat_alignment_rate", 0),
            "usedLearnedProfile": result.get("meta", {}).get("usedLearnedProfile", False) if isinstance(result.get("meta"), dict) else False,
            "usedSimilarSegments": result.get("meta", {}).get("usedSimilarSegments", False) if isinstance(result.get("meta"), dict) else False,
        },
    }
