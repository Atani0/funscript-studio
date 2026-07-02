from __future__ import annotations

from typing import Dict, List


def _nearest_segment(segments: List[Dict[str, object]], time_ms: int) -> Dict[str, object]:
    if not segments:
        return {}
    return min(segments, key=lambda item: abs(int(item.get("start", 0)) - time_ms))


def _add_candidate(candidates: List[Dict[str, object]], time_ms: int, kind: str, score: float, features: Dict[str, float]) -> None:
    if score < 0.08:
        return
    candidates.append({
        "time": max(0, int(time_ms)),
        "type": kind,
        "score": max(0.0, min(1.0, float(score))),
        "features": features,
    })


def extract_event_candidates(
    audio_events: List[Dict[str, object]],
    perception: Dict[str, object],
    profile: Dict[str, object],
    style: str = "balanced",
    audio_energy: List[float] | None = None,
    duration_ms: int = 0,
) -> List[Dict[str, object]]:
    segments = perception.get("segments", []) if isinstance(perception, dict) else []
    weights = profile.get("weights", {}) if isinstance(profile, dict) else {}
    candidates: List[Dict[str, object]] = []
    for event in audio_events:
        time_ms = int(event.get("time", 0))
        kind = str(event.get("type", "onset"))
        strength = float(event.get("strength", 0.0))
        seg = _nearest_segment(segments, time_ms) if isinstance(segments, list) else {}
        visual = seg.get("visual", {}) if isinstance(seg, dict) else {}
        interaction = seg.get("interaction", {}) if isinstance(seg, dict) else {}
        body = float(visual.get("body_motion_overall", visual.get("motion_intensity", 0.0))) if isinstance(visual, dict) else 0.0
        inter = float(interaction.get("interaction_intensity", 0.0)) if isinstance(interaction, dict) else 0.0
        audio_weight = weights.get("audio_beat", 0.6) if kind == "beat" else weights.get("audio_onset", 0.25)
        score = strength * float(audio_weight) + body * 0.22 + inter * 0.08
        if style == "beat_matched" and kind == "beat":
            score += 0.22
        if style == "smooth" and strength < 0.45:
            score *= 0.65
        _add_candidate(candidates, time_ms, kind if kind in {"beat", "onset", "peak"} else "transient", score, {
            "audio_strength": strength,
            "body_motion": body,
            "interaction": inter,
            "scene_change": 1.0 if bool(visual.get("scene_change", False)) else 0.0 if isinstance(visual, dict) else 0.0,
        })

    previous_motion = 0.0
    for seg in segments if isinstance(segments, list) else []:
        start = int(seg.get("start", 0))
        visual = seg.get("visual", {}) if isinstance(seg, dict) else {}
        interaction = seg.get("interaction", {}) if isinstance(seg, dict) else {}
        motion = float(visual.get("body_motion_overall", visual.get("motion_intensity", 0.0))) if isinstance(visual, dict) else 0.0
        hand = float(visual.get("hand_motion", 0.0)) if isinstance(visual, dict) else 0.0
        leg = float(visual.get("leg_motion", 0.0)) if isinstance(visual, dict) else 0.0
        hip = float(visual.get("hip_motion", 0.0)) if isinstance(visual, dict) else 0.0
        inter = float(interaction.get("interaction_intensity", 0.0)) if isinstance(interaction, dict) else 0.0
        scene = bool(visual.get("scene_change", False)) if isinstance(visual, dict) else False
        if motion > previous_motion + 0.18 or motion > 0.62:
            _add_candidate(candidates, start, "body_peak", motion * float(weights.get("body_motion", 0.25)) + max(hand, leg, hip) * 0.25, {
                "audio_strength": 0.0, "body_motion": motion, "interaction": inter, "scene_change": 0.0,
            })
        if inter > 0.45:
            _add_candidate(candidates, start, "interaction_peak", inter, {
                "audio_strength": 0.0, "body_motion": motion, "interaction": inter, "scene_change": 0.0,
            })
        if scene:
            _add_candidate(candidates, start, "scene_change", 0.45 + motion * 0.25, {
                "audio_strength": 0.0, "body_motion": motion, "interaction": inter, "scene_change": 1.0,
            })
        previous_motion = motion
    _add_rhythm_floor_candidates(candidates, audio_energy or [], perception, profile, style, duration_ms)
    return merge_candidates(candidates, profile, style)


def _add_rhythm_floor_candidates(
    candidates: List[Dict[str, object]],
    audio_energy: List[float],
    perception: Dict[str, object],
    profile: Dict[str, object],
    style: str,
    duration_ms: int,
) -> None:
    """Fill long low-confidence regions with audio/perception guided candidates.

    The hybrid generator is intentionally event-driven, but pure peak filtering
    can create dead openings when beat/onset detection starts late or when the
    perception layer reports low confidence. Fast generation feels better in
    those sections because it still samples the audio curve. This floor keeps
    hybrid timing alive without replacing the higher quality event candidates.
    """
    if not audio_energy or duration_ms <= 0:
        return
    timing = profile.get("timing", {}) if isinstance(profile, dict) else {}
    preferred = int(timing.get("preferred_interval_ms", 260))
    if style == "smooth":
        stride_ms = max(360, int(preferred * 1.55))
    elif style == "energetic":
        stride_ms = max(160, int(preferred * 0.75))
    else:
        stride_ms = max(220, int(preferred * 1.05))
    source_step = max(1, duration_ms // max(1, len(audio_energy) - 1))
    sample_step = max(1, round(stride_ms / source_step))
    existing_times = [int(item.get("time", 0)) for item in candidates]
    segments = perception.get("segments", []) if isinstance(perception, dict) else []

    def has_nearby_event(time_ms: int) -> bool:
        near_ms = max(260, stride_ms)
        return any(abs(time_ms - existing) <= near_ms for existing in existing_times)

    for index in range(0, len(audio_energy), sample_step):
        time_ms = min(duration_ms, int(index * duration_ms / max(1, len(audio_energy) - 1)))
        if has_nearby_event(time_ms):
            continue
        energy = max(0.0, min(1.0, float(audio_energy[index])))
        prev_energy = max(0.0, min(1.0, float(audio_energy[index - 1]))) if index > 0 else energy
        delta = max(0.0, energy - prev_energy)
        seg = _nearest_segment(segments, time_ms) if isinstance(segments, list) else {}
        visual = seg.get("visual", {}) if isinstance(seg, dict) else {}
        interaction = seg.get("interaction", {}) if isinstance(seg, dict) else {}
        body = float(visual.get("body_motion_overall", visual.get("motion_intensity", 0.0))) if isinstance(visual, dict) else 0.0
        inter = float(interaction.get("interaction_intensity", 0.0)) if isinstance(interaction, dict) else 0.0
        score = 0.19 + energy * 0.16 + delta * 0.28 + body * 0.12 + inter * 0.05
        if style == "energetic":
            score += 0.04
        if style == "smooth":
            score -= 0.03
        _add_candidate(candidates, time_ms, "rhythm_floor", score, {
            "audio_strength": max(energy, delta),
            "body_motion": body,
            "interaction": inter,
            "scene_change": 1.0 if isinstance(visual, dict) and bool(visual.get("scene_change", False)) else 0.0,
        })
        existing_times.append(time_ms)


def merge_candidates(candidates: List[Dict[str, object]], profile: Dict[str, object], style: str) -> List[Dict[str, object]]:
    timing = profile.get("timing", {}) if isinstance(profile, dict) else {}
    min_gap = int(timing.get("min_action_interval_ms", 120))
    if style == "energetic":
        min_gap = max(80, int(min_gap * 0.75))
    if style == "smooth":
        min_gap = int(min_gap * 1.35)
    ordered = sorted(candidates, key=lambda item: (int(item["time"]), -float(item["score"])))
    merged: List[Dict[str, object]] = []
    priority = {"beat": 5, "onset": 4, "peak": 4, "transient": 3, "body_peak": 2, "interaction_peak": 2, "rhythm_floor": 1.5, "scene_change": 1}
    for item in ordered:
        if not merged or int(item["time"]) - int(merged[-1]["time"]) >= min_gap:
            merged.append(item)
            continue
        current = merged[-1]
        item_rank = priority.get(str(item["type"]), 0) + float(item["score"])
        current_rank = priority.get(str(current["type"]), 0) + float(current["score"])
        if item_rank > current_rank:
            merged[-1] = item
        else:
            current["score"] = max(float(current["score"]), float(item["score"]))
    threshold = 0.16 if style == "energetic" else 0.22 if style == "balanced" else 0.28 if style == "smooth" else 0.2
    return [item for item in merged if float(item["score"]) >= threshold or item["type"] == "beat"]
