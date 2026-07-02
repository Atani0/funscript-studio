from __future__ import annotations

from typing import Dict, List, Optional


def plan_motion(
    candidates: List[Dict[str, object]],
    perception: Dict[str, object],
    profile: Dict[str, object],
    similar_segments: Optional[List[Dict[str, object]]] = None,
    style: str = "balanced",
) -> List[Dict[str, object]]:
    segments = perception.get("segments", []) if isinstance(perception, dict) else []
    amp_cfg = profile.get("amplitude", {}) if isinstance(profile, dict) else {}
    smooth_cfg = profile.get("smoothness", {}) if isinstance(profile, dict) else {}
    preferred = float(amp_cfg.get("preferred_range", 56))
    min_range = float(amp_cfg.get("min_range", 18))
    max_range = float(amp_cfg.get("max_range", 76))
    plan: List[Dict[str, object]] = []
    last_amp = preferred
    for index, event in enumerate(candidates):
        time_ms = int(event["time"])
        seg = min(segments, key=lambda item: abs(int(item.get("start", 0)) - time_ms)) if segments else {}
        visual = seg.get("visual", {}) if isinstance(seg, dict) else {}
        interaction = seg.get("interaction", {}) if isinstance(seg, dict) else {}
        shot_type = str(seg.get("shot_type", "unknown")) if isinstance(seg, dict) else "unknown"
        body = float(visual.get("body_motion_overall", visual.get("motion_intensity", 0.0))) if isinstance(visual, dict) else 0.0
        hand = float(visual.get("hand_motion", 0.0)) if isinstance(visual, dict) else 0.0
        leg = float(visual.get("leg_motion", 0.0)) if isinstance(visual, dict) else 0.0
        hip = float(visual.get("hip_motion", 0.0)) if isinstance(visual, dict) else 0.0
        inter = float(interaction.get("interaction_intensity", 0.0)) if isinstance(interaction, dict) else 0.0
        scene = 1.0 if isinstance(visual, dict) and visual.get("scene_change") else 0.0
        features = event.get("features", {}) if isinstance(event.get("features"), dict) else {}
        audio = float(features.get("audio_strength", 0.0))
        similar_adjust = 0.0
        if similar_segments:
            stats = similar_segments[0].get("script_stats", {})
            if isinstance(stats, dict):
                similar_adjust = (float(stats.get("amplitude_max", 80)) - float(stats.get("amplitude_min", 20)) - preferred) * 0.15
        density_boost = 1.12 if style == "energetic" else 0.88 if style == "smooth" else 1.0
        closeup_factor = 0.86 if shot_type in {"face_closeup", "hand_closeup"} else 0.94 if "closeup" in shot_type else 1.0
        raw_amp = (
            preferred * 0.55 +
            audio * 18 +
            body * 18 +
            max(hand, leg, hip) * 10 +
            inter * 9 +
            scene * 6 +
            similar_adjust
        ) * closeup_factor * density_boost
        # deterministic micro-variation to avoid same high/low forever
        variation = ((index * 37) % 11 - 5) * float(amp_cfg.get("variance", 0.35))
        amplitude = max(min_range, min(max_range, raw_amp + variation))
        if abs(amplitude - last_amp) < 2.0:
            amplitude += 3.0 if index % 2 else -3.0
        last_amp = amplitude
        reason = f"{event['type']} audio={audio:.2f} body={body:.2f} hip={hip:.2f}"
        plan.append({
            "time": time_ms,
            "target": "stroke",
            "intensity": max(0.0, min(1.0, float(event["score"]) + body * 0.25 + inter * 0.15)),
            "amplitude": round(max(min_range, min(max_range, amplitude)), 2),
            "direction": 1 if index % 2 else -1,
            "smoothness": float(smooth_cfg.get("ema_alpha", 0.35)),
            "reason": reason,
        })
    return plan

