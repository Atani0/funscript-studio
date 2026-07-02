"""Funscript Studio local backend.

HTTP API:
  GET  /health
  POST /analyze/audio
  POST /analyze/video
  POST /generate/funscript
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple

from audio_analysis import analyze_audio
from generator import generate, generate_from_perception, generate_hybrid
from learning.hybrid_generator import hybrid_generate_response
from learning.learned_profile import load_profile, save_profile
from learning.parameter_fitter import fit_parameters
from learning.perception_aligner import align_perception_to_script
from learning.script_feature_extractor import load_actions
from learning.similarity_index import build_similarity_index
from learning.training_dataset import add_example, load_dataset, remove_example, save_dataset, scan_directory, dataset_dir
from perception.perception_engine import analyze_perception, load_perception
from video_analysis import analyze_video

ALLOWED_ORIGINS = {
    "null",
    "file://",
}


def is_allowed_origin(origin: str) -> bool:
    if not origin:
        return True
    if origin in ALLOWED_ORIGINS:
        return True
    return (
        origin.startswith("http://127.0.0.1:")
        or origin.startswith("http://localhost:")
        or origin.startswith("http://[::1]:")
    )


def cors_origin(handler: BaseHTTPRequestHandler) -> str:
    origin = handler.headers.get("Origin", "")
    if is_allowed_origin(origin):
        return origin or "null"
    return "null"


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", cors_origin(handler))
    handler.send_header("Access-Control-Allow-Headers", "content-type")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.send_header("Vary", "Origin")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class ApiHandler(BaseHTTPRequestHandler):
    ffmpeg_path = ""
    perception_index: Dict[str, str] = {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:
        if not is_allowed_origin(self.headers.get("Origin", "")):
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", cors_origin(self))
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            json_response(self, 200, {"ok": True, "service": "funscript-backend", "ffmpeg": bool(self.ffmpeg_path)})
            return
        if self.path.startswith("/api/perception/"):
            perception_id = self.path.rsplit("/", 1)[-1]
            perception_path = self.perception_index.get(perception_id)
            if not perception_path:
                json_response(self, 404, {"error": "perception id not found"})
                return
            json_response(self, 200, load_perception(perception_path))
            return
        json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            payload = self.read_json()
            if self.path == "/analyze/audio":
                result = analyze_audio(str(payload["path"]), self.resolve_ffmpeg(payload), int(payload.get("durationMs", 0)))
                json_response(self, 200, result)
                return
            if self.path == "/analyze/video":
                result = analyze_video(str(payload["path"]), self.resolve_ffmpeg(payload))
                json_response(self, 200, {"events": result})
                return
            if self.path == "/generate/funscript":
                result = generate(
                    str(payload["path"]),
                    self.resolve_ffmpeg(payload),
                    int(payload["durationMs"]),
                    int(payload.get("stepMs", 250)),
                )
                json_response(self, 200, result)
                return
            if self.path == "/api/perception/analyze":
                video_path = str(payload.get("videoPath") or payload.get("path") or "")
                if not video_path:
                    raise RuntimeError("videoPath is required")
                output_dir = os.environ.get("FUNSCRIPT_STUDIO_DATA_DIR") or os.path.join(os.getcwd(), "funscript-studio-data")
                perception = analyze_perception(
                    video_path=video_path,
                    ffmpeg_path=self.resolve_ffmpeg(payload),
                    quality=str(payload.get("quality", "balanced")),
                    audio_mode=str(payload.get("audioMode", "auto")),
                    visual_mode=str(payload.get("visualMode", "auto")),
                    save_debug_frames=bool(payload.get("saveDebugFrames", False)),
                    output_dir=output_dir,
                )
                perception_id = str(perception.get("id"))
                self.perception_index[perception_id] = str(perception.get("perceptionPath"))
                summary = perception.get("summary", {})
                json_response(self, 200, {"ok": True, "id": perception_id, "perceptionPath": perception.get("perceptionPath"), "summary": summary})
                return
            if self.path == "/api/generate/from-perception":
                perception_path = str(payload.get("perceptionPath") or "")
                if not perception_path:
                    perception_id = str(payload.get("id") or "")
                    perception_path = self.perception_index.get(perception_id, "")
                if not perception_path:
                    raise RuntimeError("perceptionPath or id is required")
                result = generate_from_perception(
                    perception_path,
                    str(payload.get("axis", "stroke")),
                    str(payload.get("profile", "balanced")),
                )
                json_response(self, 200, result)
                return
            if self.path == "/api/generate/hybrid":
                video_path = str(payload.get("videoPath") or payload.get("path") or "")
                if not video_path:
                    raise RuntimeError("videoPath is required")
                result = hybrid_generate_response(
                    video_path=video_path,
                    ffmpeg_path=self.resolve_ffmpeg(payload),
                    perception_path=str(payload.get("perceptionPath") or ""),
                    profile_path=str(payload.get("profilePath") or ""),
                    dataset_name=str(payload.get("datasetName") or ""),
                    mode=str(payload.get("mode") or "hybrid"),
                    style=str(payload.get("style") or "balanced"),
                    axis=str(payload.get("axis") or "stroke"),
                )
                json_response(self, 200, result)
                return
            if self.path == "/api/learning/dataset/add":
                result = add_example(
                    str(payload.get("datasetName") or "default"),
                    str(payload.get("videoPath") or ""),
                    str(payload.get("funscriptPath") or ""),
                    str(payload.get("perceptionPath") or ""),
                    payload.get("tags") if isinstance(payload.get("tags"), list) else [],
                )
                json_response(self, 200, {"ok": True, "dataset": result})
                return
            if self.path == "/api/learning/dataset/scan":
                result = scan_directory(str(payload.get("datasetName") or "default"), str(payload.get("directory") or ""))
                json_response(self, 200, {"ok": True, "dataset": result})
                return
            if self.path == "/api/learning/dataset/remove":
                result = remove_example(str(payload.get("datasetName") or "default"), str(payload.get("exampleId") or ""))
                json_response(self, 200, {"ok": True, "dataset": result})
                return
            if self.path == "/api/learning/train":
                dataset_name = str(payload.get("datasetName") or "default")
                dataset = load_dataset(dataset_name)
                samples = []
                actions_by_example = {}
                for example in dataset.get("examples", []):
                    perception_path = str(example.get("perception_path") or "")
                    if not perception_path:
                        continue
                    actions = load_actions(str(example.get("funscript_path") or ""))
                    actions_by_example[str(example.get("id"))] = actions
                    perception = load_perception(perception_path)
                    aligned = align_perception_to_script(perception, actions)
                    for item in aligned:
                        item["example_id"] = str(example.get("id"))
                    samples.extend(aligned)
                out_dir = str(dataset_dir(dataset_name))
                report = fit_parameters(samples, dataset_name, out_dir)
                index = build_similarity_index(samples, actions_by_example, os.path.join(out_dir, "similarity_index.json"))
                json_response(self, 200, {"ok": True, "report": report, "segments": len(index.get("segments", []))})
                return
            json_response(self, 404, {"error": "not found"})
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def resolve_ffmpeg(self, payload: Dict[str, Any]) -> str:
        ffmpeg = str(payload.get("ffmpeg") or self.ffmpeg_path or os.environ.get("FFMPEG_PATH") or "")
        if not ffmpeg:
            raise RuntimeError("FFmpeg path is not configured")
        return ffmpeg


def serve(host: str, port: int, ffmpeg: str) -> Tuple[ThreadingHTTPServer, int]:
    ApiHandler.ffmpeg_path = ffmpeg
    server = ThreadingHTTPServer((host, port), ApiHandler)
    return server, int(server.server_address[1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("--ffmpeg", default=os.environ.get("FFMPEG_PATH", ""))
    args = parser.parse_args()
    server, actual_port = serve(args.host, args.port, args.ffmpeg)
    print(json.dumps({"endpoint": f"http://{args.host}:{actual_port}", "port": actual_port, "ws": None}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
