from __future__ import annotations

from typing import Dict, List

from .perception_schema import clamp01, empty_segment, safe_float


def nearest(items: List[Dict[str, object]], time_ms: int, key: str = "time") -> Dict[str, object]:
    if not items:
        return {}
    return min(items, key=lambda item: abs(int(item.get(key, 0)) - time_ms))


def select_strategy(style: str) -> Dict[str, float]:
    if style == "live_action":
        return {"audio": 0.25, "visual": 0.25, "pose": 0.35, "interaction": 0.15}
    if style == "animation_3d":
        return {"audio": 0.3, "visual": 0.35, "pose": 0.25, "interaction": 0.10}
    if style == "anime_2d":
        return {"audio": 0.4, "visual": 0.5, "pose": 0.0, "interaction": 0.10}
    return {"audio": 0.4, "visual": 0.4, "pose": 0.2, "interaction": 0.0}


def fuse_features(
    duration_ms: int,
    style: Dict[str, object],
    visual_frames: List[Dict[str, object]],
    pose_frames: List[Dict[str, object]],
    shot_frames: List[Dict[str, object]],
    interaction_frames: List[Dict[str, object]],
    audio_result: Dict[str, object],
    segment_ms: int = 250,
) -> Dict[str, object]:
    style_name = str(style.get("style", "unknown"))
    strategy = select_strategy(style_name)
    audio_samples = audio_result.get("samples", [])
    segments: List[Dict[str, object]] = []
    for start in range(0, max(duration_ms, segment_ms), segment_ms):
        end = min(duration_ms, start + segment_ms)
        segment = empty_segment(start, end)
        visual = nearest(visual_frames, start)
        pose = nearest(pose_frames, start)
        shot = nearest(shot_frames, start)
        interaction = nearest(interaction_frames, start).get("interaction", {})
        audio = nearest(audio_samples, start)
        audio_core = audio.get("audio", {}) if isinstance(audio, dict) else {}
        audio_event = audio.get("audio_event", {}) if isinstance(audio, dict) else {}
        body_motion = pose.get("body_motion", {}) if isinstance(pose, dict) else {}
        pose_conf = safe_float(pose.get("confidence", 0.0)) if isinstance(pose, dict) else 0.0
        visual_motion = clamp01(safe_float(visual.get("motion", 0.0))) if isinstance(visual, dict) else 0.0
        body_overall = clamp01(safe_float(body_motion.get("overall", 0.0))) if isinstance(body_motion, dict) else 0.0
        interaction_intensity = clamp01(safe_float(interaction.get("interaction_intensity", 0.0))) if isinstance(interaction, dict) else 0.0
        beat = clamp01(safe_float(audio_core.get("beat_strength", 0.0))) if isinstance(audio_core, dict) else 0.0
        onset = clamp01(safe_float(audio_core.get("onset", 0.0))) if isinstance(audio_core, dict) else 0.0
        transient = clamp01(safe_float(audio_event.get("transient_strength", 0.0))) if isinstance(audio_event, dict) else 0.0
        pose_weight = strategy["pose"] if pose_conf > 0.35 else strategy["pose"] * 0.25
        intensity = clamp01(
            strategy["visual"] * visual_motion +
            pose_weight * body_overall +
            strategy["audio"] * max(beat, onset, transient) +
            strategy["interaction"] * interaction_intensity
        )
        segment["style"] = style_name
        segment["shot_type"] = shot.get("shot_type", "unknown") if isinstance(shot, dict) else "unknown"
        segment["confidence"] = clamp01((safe_float(style.get("confidence", 0.0)) + pose_conf + safe_float(shot.get("confidence", 0.0) if isinstance(shot, dict) else 0.0)) / 3)
        segment["visual"] = {
            "motion_intensity": visual_motion,
            "body_motion_overall": body_overall,
            "upper_body_motion": clamp01(safe_float(body_motion.get("upper_body", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "lower_body_motion": clamp01(safe_float(body_motion.get("lower_body", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "hand_motion": clamp01(safe_float(body_motion.get("hands", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "leg_motion": clamp01(safe_float(body_motion.get("legs", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "hip_motion": clamp01(safe_float(body_motion.get("hips", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "torso_motion": clamp01(safe_float(body_motion.get("torso", 0.0))) if isinstance(body_motion, dict) else 0.0,
            "scene_change": bool(visual.get("scene_change", False)) if isinstance(visual, dict) else False,
        }
        segment["interaction"] = {
            "person_count": int(interaction.get("person_count", 0)) if isinstance(interaction, dict) else 0,
            "interaction_intensity": interaction_intensity,
            "proximity": clamp01(safe_float(interaction.get("proximity", 0.0))) if isinstance(interaction, dict) else 0.0,
            "sync_motion": clamp01(safe_float(interaction.get("sync_motion", 0.0))) if isinstance(interaction, dict) else 0.0,
            "contact_likelihood": clamp01(max(safe_float(interaction.get("hand_contact_likelihood", 0.0)), safe_float(interaction.get("body_contact_likelihood", 0.0)))) if isinstance(interaction, dict) else 0.0,
        }
        segment["audio"] = {
            "mode": audio_result.get("mode", "unknown"),
            "beat_strength": beat,
            "onset_strength": onset,
            "transient_strength": transient,
            "clap_likelihood": clamp01(safe_float(audio_event.get("clap_likelihood", 0.0))) if isinstance(audio_event, dict) else 0.0,
            "tempo_confidence": clamp01(safe_float(audio_core.get("tempo_confidence", 0.0))) if isinstance(audio_core, dict) else 0.0,
        }
        segment["suggested_motion"] = {
            "intensity": intensity,
            "rhythm_density": clamp01(max(beat, onset, transient)),
            "smoothness": clamp01(1.0 - abs(onset - visual_motion) * 0.5),
            "accent": clamp01(max(beat, transient, 1.0 if segment["visual"]["scene_change"] else 0.0)),
        }
        segment["explain"] = [f"strategy={strategy}", f"style={style_name}", f"pose_conf={pose_conf:.2f}"]
        segments.append(segment)
    avg_motion = sum(float(seg["suggested_motion"]["intensity"]) for seg in segments) / max(1, len(segments))  # type: ignore[index]
    avg_interaction = sum(float(seg["interaction"]["interaction_intensity"]) for seg in segments) / max(1, len(segments))  # type: ignore[index]
    return {
        "version": "1.0",
        "duration": duration_ms,
        "style": style,
        "audioSummary": {"mode": audio_result.get("mode", "unknown"), "tempo": audio_result.get("tempo", 0), "tempoConfidence": audio_result.get("tempo_confidence", 0.0)},
        "segments": segments,
        "raw": {"visual": visual_frames, "pose": pose_frames, "shot": shot_frames, "interaction": interaction_frames, "audio": audio_result},
        "summary": {
            "duration": duration_ms,
            "style": style_name,
            "avgMotion": avg_motion,
            "avgInteraction": avg_interaction,
            "audioMode": audio_result.get("mode", "unknown"),
            "confidence": style.get("confidence", 0.0),
        },
    }
