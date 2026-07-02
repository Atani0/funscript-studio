"""Event-driven visual motion extraction using OpenCV or FFmpeg fallback."""

from __future__ import annotations

import re
import subprocess
from typing import Dict, List


SCENE_PATTERN = re.compile(r"pts_time:([\d.]+).*?lavfi\.scene_score=([\d.]+)", re.DOTALL)


def _normalize_points(points: List[Dict[str, float]]) -> List[Dict[str, float]]:
    if not points:
        return []
    values = [point["motion"] for point in points]
    low, high = min(values), max(values)
    if high <= low:
        for point in points:
            point["motion"] = 0.5
        return points
    for point in points:
        point["motion"] = max(0.0, min(1.0, (point["motion"] - low) / (high - low)))
    return points


def _opencv_motion(video_path: str, sample_fps: float = 6.0) -> List[Dict[str, float]]:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return []

    capture = cv2.VideoCapture(video_path)
    source_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, round(source_fps / sample_fps))
    points: List[Dict[str, float]] = []
    previous = None
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % stride == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 90))
            if previous is not None:
                difference = float(np.mean(cv2.absdiff(gray, previous))) / 255.0
                flow_motion = difference
                try:
                    flow = cv2.calcOpticalFlowFarneback(previous, gray, None, 0.5, 2, 15, 2, 5, 1.1, 0)
                    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    flow_motion = max(difference, min(1.0, float(np.mean(magnitude)) / 3.0))
                except Exception:
                    pass
                points.append({"time": frame_index / source_fps, "motion": flow_motion, "scene_change": difference > 0.18})
            previous = gray
        frame_index += 1
    capture.release()
    return _normalize_points(points)


def _ffmpeg_motion(video_path: str, ffmpeg_path: str) -> List[Dict[str, float]]:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-i",
        video_path,
        "-vf",
        "fps=4,select='gte(scene,0)',metadata=print",
        "-an",
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
    return [
        {"time": float(match.group(1)), "motion": min(1.0, float(match.group(2)) * 4.0), "scene_change": float(match.group(2)) > 0.32}
        for match in SCENE_PATTERN.finditer(completed.stderr)
    ]


def analyze_video(video_path: str, ffmpeg_path: str) -> List[Dict[str, float]]:
    return _opencv_motion(video_path) or _ffmpeg_motion(video_path, ffmpeg_path)
