from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .audio_analyzer import AudioAnalyzer
from .feature_fusion import fuse_features
from .frame_sampler import sample_frames
from .interaction_analyzer import InteractionAnalyzer
from .multi_person_tracker import MultiPersonTracker
from .perception_schema import load_json, save_json
from .pose_analyzer import PoseAnalyzer
from .shot_analyzer import ShotAnalyzer
from .style_classifier import classify_style
from .visual_analyzer import VisualAnalyzer


def probe_duration_ms(video_path: str, ffmpeg_path: str) -> int:
    try:
        completed = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-i", video_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        import re
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", completed.stderr)
        if not match:
            return 0
        hours, minutes, seconds = int(match.group(1)), int(match.group(2)), float(match.group(3))
        return int((hours * 3600 + minutes * 60 + seconds) * 1000)
    except Exception:
        return 0


def analyze_perception(
    video_path: str,
    ffmpeg_path: str,
    quality: str = "balanced",
    audio_mode: str = "auto",
    visual_mode: str = "auto",
    save_debug_frames: bool = False,
    output_dir: str | Path = "perception_outputs",
    progress: Optional[Callable[[float], None]] = None,
) -> Dict[str, Any]:
    duration_ms = probe_duration_ms(video_path, ffmpeg_path)
    visual_analyzer = VisualAnalyzer()
    pose_analyzer = PoseAnalyzer()
    shot_analyzer = ShotAnalyzer()
    tracker = MultiPersonTracker()
    interaction_analyzer = InteractionAnalyzer()
    visual_frames = []
    pose_frames = []
    shot_frames = []
    interaction_frames = []
    frame_features = []
    errors = []

    try:
        for sample in sample_frames(video_path, quality, progress):
            duration_ms = max(duration_ms, sample.timestamp_ms)
            visual = visual_analyzer.analyze(sample)
            pose = pose_analyzer.analyze(sample, visual)
            detections = [
                {"bbox": person.get("bbox", [0.25, 0.2, 0.5, 0.6]), "confidence": person.get("pose_confidence", pose.get("confidence", 0.2))}
                for person in pose.get("persons", [])
            ]
            tracks = tracker.update(sample.timestamp_ms, detections)
            shot = shot_analyzer.analyze(sample.timestamp_ms, pose, visual)
            interaction = interaction_analyzer.analyze(sample.timestamp_ms, tracks, pose)
            visual_frames.append(visual)
            pose_frames.append(pose)
            shot_frames.append(shot)
            interaction_frames.append(interaction)
            if isinstance(visual.get("frame_features"), dict):
                frame_features.append(visual["frame_features"])
    except Exception as exc:
        errors.append(str(exc))

    style = classify_style(frame_features)
    audio = AudioAnalyzer().analyze(video_path, ffmpeg_path, duration_ms, audio_mode)
    perception = fuse_features(duration_ms, style, visual_frames, pose_frames, shot_frames, interaction_frames, audio)
    perception["source"] = {"videoPath": video_path, "quality": quality, "audioMode": audio_mode, "visualMode": visual_mode}
    perception["errors"] = errors + audio.get("errors", [])
    perception_id = hashlib.sha1((video_path + str(duration_ms) + quality).encode("utf-8", "ignore")).hexdigest()[:12]
    out_dir = Path(output_dir)
    path = save_json(perception, out_dir, f"perception_{perception_id}")
    perception["perceptionPath"] = path
    perception["id"] = Path(path).stem
    return perception


def load_perception(path: str) -> Dict[str, Any]:
    return load_json(path)
