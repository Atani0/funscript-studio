from __future__ import annotations

import re
import subprocess
from typing import Dict, List

from .perception_schema import clamp01, normalize, safe_float, smooth


RMS_PATTERN = re.compile(r"RMS_level=([^\s\r\n]+)")


class AudioAnalyzer:
    def analyze(
        self,
        video_path: str,
        ffmpeg_path: str,
        duration_ms: int,
        mode: str = "auto",
        step_ms: int = 100,
    ) -> Dict[str, object]:
        envelope = self._rms_envelope(video_path, ffmpeg_path)
        if not envelope:
            return {
                "mode": "unknown",
                "tempo": 0,
                "tempo_confidence": 0.0,
                "samples": [],
                "events": [],
                "errors": ["audio track missing or ffmpeg audio analysis failed"],
            }

        rms = smooth(normalize(envelope), 0.4)
        onsets = [0.0] + [max(0.0, rms[i] - rms[i - 1]) for i in range(1, len(rms))]
        onsets = smooth(normalize(onsets), 0.45)
        high_transient = [clamp01(value * 1.35) for value in onsets]
        low_energy = smooth(rms, 0.7)
        sample_count = max(len(rms), 1)
        inferred_step = max(1, duration_ms // max(1, sample_count - 1)) if duration_ms else step_ms
        beat_indices = self._detect_peaks(rms, onsets, inferred_step)
        intervals = [beat_indices[i] - beat_indices[i - 1] for i in range(1, len(beat_indices))]
        tempo = 0
        tempo_confidence = 0.0
        if intervals:
            median_interval = sorted(intervals)[len(intervals) // 2] * inferred_step
            if median_interval > 0:
                tempo = round(60000 / median_interval)
                tempo_confidence = clamp01(len(intervals) / 16)

        audio_mode = self._select_mode(mode, tempo_confidence, onsets)
        samples: List[Dict[str, object]] = []
        events: List[Dict[str, object]] = []
        beat_set = set(beat_indices)
        rhythm = self._rhythmic_repetition(beat_indices, len(rms))
        for index, value in enumerate(rms):
            time_ms = min(duration_ms, index * inferred_step) if duration_ms else index * inferred_step
            onset = onsets[index]
            transient = high_transient[index]
            beat_strength = 1.0 if index in beat_set else max(0.0, onset * 0.7)
            clap = clamp01(transient * (0.4 + rhythm * 0.6))
            impact = clamp01(transient * (1.0 - low_energy[index] * 0.35))
            samples.append({
                "time": time_ms,
                "audio": {
                    "rms": value,
                    "onset": onset,
                    "beat_strength": beat_strength,
                    "low_energy": low_energy[index],
                    "high_transient": transient,
                    "tempo_confidence": tempo_confidence,
                },
                "audio_event": {
                    "transient_strength": transient,
                    "clap_likelihood": clap,
                    "impact_likelihood": impact,
                    "rhythmic_repetition": rhythm,
                },
            })
            if transient > 0.62 or index in beat_set:
                events.append({"time": time_ms, "type": "beat" if index in beat_set else "transient", "strength": max(beat_strength, transient)})

        return {"mode": audio_mode, "tempo": tempo, "tempo_confidence": tempo_confidence, "samples": samples, "events": events}

    def _rms_envelope(self, video_path: str, ffmpeg_path: str) -> List[float]:
        command = [
            ffmpeg_path,
            "-hide_banner",
            "-i",
            video_path,
            "-vn",
            "-af",
            "asetnsamples=n=4410:p=0,astats=metadata=1:reset=1,ametadata=print",
            "-f",
            "null",
            "-",
        ]
        completed = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", check=False)
        if completed.returncode != 0:
            return []
        values = []
        for match in RMS_PATTERN.finditer(completed.stderr):
            raw = match.group(1).strip()
            db = safe_float(raw, default=float("nan"))
            if db != db:
                continue
            values.append(db)
        return [clamp01((db + 65.0) / 65.0) for db in values]

    def _detect_peaks(self, rms: List[float], onsets: List[float], step_ms: int) -> List[int]:
        peaks: List[int] = []
        min_gap = max(2, round(180 / max(1, step_ms)))
        last = -10**9
        for index in range(1, len(rms) - 1):
            score = 0.55 * onsets[index] + 0.45 * rms[index]
            if score < 0.55:
                continue
            if score >= 0.55 * onsets[index - 1] + 0.45 * rms[index - 1] and score >= 0.55 * onsets[index + 1] + 0.45 * rms[index + 1]:
                if index - last >= min_gap:
                    peaks.append(index)
                    last = index
        return peaks

    def _rhythmic_repetition(self, peaks: List[int], length: int) -> float:
        if len(peaks) < 4:
            return 0.0
        intervals = [peaks[i] - peaks[i - 1] for i in range(1, len(peaks))]
        avg = sum(intervals) / len(intervals)
        if avg <= 0:
            return 0.0
        variance = sum(abs(item - avg) for item in intervals) / len(intervals)
        return clamp01(1.0 - variance / max(avg, 1.0))

    def _select_mode(self, requested: str, tempo_confidence: float, onsets: List[float]) -> str:
        if requested in {"music", "event"}:
            return requested
        transient_density = sum(1 for value in onsets if value > 0.55) / max(1, len(onsets))
        if tempo_confidence > 0.45:
            return "music"
        if transient_density > 0.08:
            return "event"
        if tempo_confidence > 0.25 and transient_density > 0.04:
            return "mixed"
        return "unknown"
