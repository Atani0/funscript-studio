"""Event-driven audio analysis.

Zero-setup default: FFmpeg log parsing. Optional scientific stacks can be
added later without changing the HTTP API.
"""

from __future__ import annotations

import re
import subprocess
from statistics import median
from typing import Dict, List


RMS_PATTERN = re.compile(r"RMS_level=([^\s\r\n]+)")


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "+"):
            return default
        parsed = float(value)
        if parsed != parsed or parsed in (float("inf"), float("-inf")):
            return default
        return parsed
    except Exception:
        return default


def _normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high <= low:
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def percentile(values: List[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * ratio)))
    return ordered[index]


def detect_peaks(values: List[float], times: List[int], threshold: float, min_distance_ms: int) -> List[int]:
    peaks: List[int] = []
    last_time = -10**12
    for index in range(1, len(values) - 1):
        value = values[index]
        if value < threshold or value < values[index - 1] or value < values[index + 1]:
            continue
        if times[index] - last_time < min_distance_ms:
            if peaks and value > values[peaks[-1]]:
                peaks[-1] = index
                last_time = times[index]
            continue
        peaks.append(index)
        last_time = times[index]
    return peaks


def analyze_audio_curve(video_path: str, ffmpeg_path: str) -> List[float]:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-i",
        video_path,
        "-vn",
        "-af",
        "asetnsamples=n=22050:p=0,astats=metadata=1:reset=1,ametadata=print",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return []
    decibels = []
    for match in RMS_PATTERN.finditer(completed.stderr):
        db = safe_float(match.group(1).strip(), default=float("nan"))
        if db != db:
            continue
        decibels.append(db)
    linear = [max(0.0, min(1.0, (db + 60.0) / 60.0)) for db in decibels]
    return _normalize(linear)


def analyze_audio(video_path: str, ffmpeg_path: str, duration_ms: int = 0, step_ms: int = 250) -> Dict[str, object]:
    energy = analyze_audio_curve(video_path, ffmpeg_path)
    if not energy:
        return {"energy": [], "events": []}
    if duration_ms <= 0:
        duration_ms = max(1, len(energy) * step_ms)
    times = [min(duration_ms, index * duration_ms // max(1, len(energy) - 1)) for index in range(len(energy))]
    deltas = [0.0] + [max(0.0, energy[index] - energy[index - 1]) for index in range(1, len(energy))]
    peak_threshold = max(0.62, percentile(energy, 0.78))
    onset_threshold = max(0.18, percentile(deltas, 0.84))
    peak_indices = detect_peaks(energy, times, peak_threshold, 220)
    onset_indices = detect_peaks(deltas, times, onset_threshold, 160)
    events: List[Dict[str, object]] = []
    for index in peak_indices:
        events.append({"time": times[index], "type": "peak", "strength": round(float(energy[index]), 4)})
    for index in onset_indices:
        events.append({"time": times[index], "type": "onset", "strength": round(float(deltas[index]), 4)})

    gaps = [
        times[peak_indices[index]] - times[peak_indices[index - 1]]
        for index in range(1, len(peak_indices))
        if 260 <= times[peak_indices[index]] - times[peak_indices[index - 1]] <= 1200
    ]
    if len(gaps) >= 2:
        beat_gap = int(median(gaps))
        start = times[peak_indices[0]]
        for beat_time in range(start, duration_ms + 1, max(1, beat_gap)):
            nearest = min((times[index] for index in peak_indices), key=lambda value: abs(value - beat_time), default=beat_time)
            strength = max(0.45, 1.0 - abs(nearest - beat_time) / max(beat_gap, 1))
            events.append({"time": beat_time, "type": "beat", "strength": round(float(strength), 4)})

    events.sort(key=lambda event: int(event["time"]))
    return {"energy": energy, "events": events}
