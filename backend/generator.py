"""Event-driven motion engine: audio events + visual events -> funscript."""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List, Optional

from audio_analysis import analyze_audio
from video_analysis import analyze_video
try:
    from perception.perception_schema import load_json
except Exception:
    load_json = None  # type: ignore


def normalize(values: List[float]) -> List[float]:
    if not values:
        return values
    low, high = min(values), max(values)
    if high <= low:
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def nearest_visual(points: List[Dict[str, float]], seconds: float) -> Dict[str, float]:
    if not points:
        return {"motion": 0.0, "scene_change": False}
    return min(points, key=lambda point: abs(point["time"] - seconds))


def event_strength(events: List[Dict[str, object]], time_ms: int, event_type: Optional[str] = None, radius_ms: int = 220) -> float:
    strength = 0.0
    for event in events:
        if event_type is not None and event.get("type") != event_type:
            continue
        distance = abs(int(event["time"]) - time_ms)
        if distance > radius_ms:
            continue
        falloff = 1.0 - distance / radius_ms
        strength = max(strength, float(event["strength"]) * falloff)
    return max(0.0, min(1.0, strength))


def smooth_peak_preserving(values: List[float], alpha: float) -> List[float]:
    if not values:
        return []
    output: List[float] = []
    ema = values[0]
    for index, value in enumerate(values):
        ema = alpha * value + (1.0 - alpha) * ema
        previous_value = values[index - 1] if index > 0 else value
        next_value = values[index + 1] if index < len(values) - 1 else value
        is_peak = value > 0.62 and value >= previous_value and value >= next_value
        output.append(max(ema, value * 0.92) if is_peak else ema)
    return output


def motion_to_position(value: float, index: int) -> int:
    amplitude = 18.0 + max(0.0, min(1.0, value)) * 38.0
    direction = -1 if index % 2 == 0 else 1
    return round(max(0.0, min(100.0, 50.0 + direction * amplitude)))


def reduce_actions(actions: List[Dict[str, object]], tolerance: int = 2) -> List[Dict[str, object]]:
    if len(actions) <= 2:
        return actions
    reduced = [actions[0]]
    for index in range(1, len(actions) - 1):
        previous = reduced[-1]
        current = actions[index]
        next_action = actions[index + 1]
        span = max(1, int(next_action["at"]) - int(previous["at"]))
        linear = int(previous["pos"]) + (int(next_action["pos"]) - int(previous["pos"])) * (int(current["at"]) - int(previous["at"])) / span
        if abs(int(current["pos"]) - linear) > tolerance or abs(int(current["pos"]) - int(previous["pos"])) > 10:
            reduced.append(current)
    reduced.append(actions[-1])
    return reduced


def generate(video_path: str, ffmpeg_path: str, duration_ms: int, step_ms: int = 250, alpha: float = 0.35) -> Dict[str, object]:
    audio_result = analyze_audio(video_path, ffmpeg_path, duration_ms, step_ms)
    audio_events = audio_result["events"]
    visual_points = analyze_video(video_path, ffmpeg_path)
    count = max(2, math.ceil(duration_ms / step_ms))
    raw_motion: List[float] = []

    for index in range(count):
        time_ms = min(duration_ms, index * step_ms)
        visual = nearest_visual(visual_points, time_ms / 1000.0)
        audio_value = event_strength(audio_events, time_ms, None, 240)
        beat_boost = event_strength(audio_events, time_ms, "beat", 120)
        visual_value = float(visual.get("motion", 0.0)) + (0.18 if visual.get("scene_change") else 0.0)
        raw_motion.append(0.46 * audio_value + 0.34 * visual_value + 0.14 * beat_boost)

    scaled = normalize(raw_motion)
    smoothed = smooth_peak_preserving(scaled, alpha)
    actions: List[Dict[str, object]] = []
    for index, value in enumerate(smoothed):
        actions.append({"at": min(duration_ms, index * step_ms), "pos": motion_to_position(value, index), "easing": "smooth"})

    return {
        "version": "1.0",
        "inverted": False,
        "range": 100,
        "actions": reduce_actions(actions),
        "meta": {
            "engine": "event-driven-python-opencv" if visual_points else "event-driven-python-ffmpeg",
            "stepMs": step_ms,
            "audioEvents": len(audio_events),
            "videoEvents": len(visual_points),
            "peaks": sum(
                1
                for index, value in enumerate(smoothed)
                if value > (smoothed[index - 1] if index else 0)
                and value > (smoothed[index + 1] if index < len(smoothed) - 1 else 0)
            ),
        },
    }


def generate_from_perception(perception_path: str, axis: str = "stroke", profile: str = "balanced") -> Dict[str, object]:
    if load_json is None:
        raise RuntimeError("perception loader unavailable")
    perception = load_json(perception_path)
    segments = perception.get("segments", [])
    if not segments:
        raise RuntimeError("perception JSON has no segments")
    profile_gain = {
        "smooth": 0.75,
        "balanced": 1.0,
        "energetic": 1.25,
        "beat_matched": 1.1,
    }.get(profile, 1.0)
    actions: List[Dict[str, object]] = []
    last_pos = 50
    direction = -1
    for index, segment in enumerate(segments):
        suggested = segment.get("suggested_motion", {})
        audio = segment.get("audio", {})
        visual = segment.get("visual", {})
        intensity = max(
            float(suggested.get("intensity", 0.0)),
            float(audio.get("beat_strength", 0.0)) * 0.9 if profile == "beat_matched" else 0.0,
            float(visual.get("body_motion_overall", 0.0)) * 0.85,
        )
        accent = float(suggested.get("accent", 0.0))
        amplitude = max(10.0, min(48.0, (18.0 + intensity * 34.0 + accent * 10.0) * profile_gain))
        if profile == "smooth":
            direction = -direction if index % 2 == 0 else direction
        else:
            direction *= -1
        pos = round(max(0.0, min(100.0, 50.0 + direction * amplitude)))
        at = int(segment.get("start", index * 250))
        if abs(pos - last_pos) < 3 and accent < 0.6:
            continue
        actions.append({"at": at, "pos": pos})
        last_pos = pos
    duration = int(perception.get("duration", actions[-1]["at"] if actions else 0))
    if not actions or actions[0]["at"] != 0:
        actions.insert(0, {"at": 0, "pos": 50})
    if actions[-1]["at"] < duration:
        actions.append({"at": duration, "pos": 50})
    return {
        "version": "1.0",
        "inverted": False,
        "range": 100,
        "actions": reduce_actions(actions, 2),
        "meta": {
            "engine": "perception-driven-generator",
            "profile": profile,
            "axis": axis,
            "segments": len(segments),
        },
    }


def generate_hybrid(
    video_path: str,
    ffmpeg_path: str,
    perception_path: str = "",
    profile_path: str = "",
    dataset_name: str = "",
    mode: str = "hybrid",
    style: str = "balanced",
    axis: str = "stroke",
) -> Dict[str, object]:
    from learning.hybrid_generator import hybrid_generate
    return hybrid_generate(
        video_path=video_path,
        ffmpeg_path=ffmpeg_path,
        perception_path=perception_path,
        profile_path=profile_path,
        dataset_name=dataset_name,
        mode=mode,
        style=style,
        axis=axis,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--duration-ms", required=True, type=int)
    parser.add_argument("--step-ms", default=250, type=int)
    parser.add_argument("--perception")
    parser.add_argument("--profile", default="balanced")
    args = parser.parse_args()
    if args.perception:
        result = generate_from_perception(args.perception, "stroke", args.profile)
    else:
        result = generate(args.video, args.ffmpeg, args.duration_ms, args.step_ms)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
