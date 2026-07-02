from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional


DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "training_datasets"


def dataset_dir(dataset_name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in dataset_name) or "default"
    return DATA_ROOT / safe


def load_dataset(dataset_name: str) -> Dict[str, object]:
    path = dataset_dir(dataset_name) / "dataset.json"
    if not path.exists():
        return {"dataset_name": dataset_name, "examples": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_dataset(dataset: Dict[str, object]) -> str:
    root = dataset_dir(str(dataset.get("dataset_name", "default")))
    root.mkdir(parents=True, exist_ok=True)
    path = root / "dataset.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def add_example(dataset_name: str, video_path: str, funscript_path: str, perception_path: str = "", tags: Optional[List[str]] = None) -> Dict[str, object]:
    dataset = load_dataset(dataset_name)
    examples = dataset.setdefault("examples", [])
    assert isinstance(examples, list)
    examples.append({
        "id": f"example_{uuid.uuid4().hex[:10]}",
        "video_path": video_path,
        "funscript_path": funscript_path,
        "perception_path": perception_path,
        "tags": tags or [],
    })
    save_dataset(dataset)
    return dataset


def remove_example(dataset_name: str, example_id: str) -> Dict[str, object]:
    dataset = load_dataset(dataset_name)
    dataset["examples"] = [ex for ex in dataset.get("examples", []) if ex.get("id") != example_id]
    save_dataset(dataset)
    return dataset


def scan_directory(dataset_name: str, directory: str) -> Dict[str, object]:
    dataset = load_dataset(dataset_name)
    examples = dataset.setdefault("examples", [])
    assert isinstance(examples, list)
    files = list(Path(directory).glob("**/*"))
    videos = [item for item in files if item.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".avi"}]
    for video in videos:
        script = video.with_suffix(".funscript")
        if script.exists():
            examples.append({
                "id": f"example_{uuid.uuid4().hex[:10]}",
                "video_path": str(video),
                "funscript_path": str(script),
                "perception_path": "",
                "tags": [],
            })
    save_dataset(dataset)
    return dataset
