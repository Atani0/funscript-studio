from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generator, Optional


QUALITY_FPS = {
    "fast": 5.0,
    "balanced": 10.0,
    "high_quality": 15.0,
}


@dataclass
class FrameSample:
    frame_index: int
    timestamp_ms: int
    image: object
    original_fps: float
    analysis_fps: float
    width: int
    height: int


def sample_frames(
    video_path: str,
    quality: str = "balanced",
    progress: Optional[Callable[[float], None]] = None,
) -> Generator[FrameSample, None, None]:
    """Stream frames at an analysis FPS without loading the whole video."""
    try:
        import cv2  # type: ignore
    except Exception as exc:
        raise RuntimeError("OpenCV is unavailable; frame sampling cannot run") from exc

    analysis_fps = QUALITY_FPS.get(quality, QUALITY_FPS["balanced"])
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    original_fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    stride = max(1, round(original_fps / analysis_fps))
    frame_index = 0

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % stride == 0:
                timestamp_ms = int(round(frame_index / max(original_fps, 1.0) * 1000))
                if progress and total_frames > 0:
                    progress(min(1.0, frame_index / total_frames))
                yield FrameSample(frame_index, timestamp_ms, frame, original_fps, analysis_fps, width, height)
            frame_index += 1
    finally:
        capture.release()
        if progress:
            progress(1.0)
