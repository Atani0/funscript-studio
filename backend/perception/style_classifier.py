from __future__ import annotations

from typing import Dict, List

from .perception_schema import clamp01


def classify_style(frame_features: List[Dict[str, float]]) -> Dict[str, object]:
    if not frame_features:
        return {"style": "unknown", "confidence": 0.0, "reason": "no visual frames"}

    edge = sum(item.get("edge_density", 0.0) for item in frame_features) / len(frame_features)
    saturation = sum(item.get("saturation", 0.0) for item in frame_features) / len(frame_features)
    texture = sum(item.get("texture_complexity", 0.0) for item in frame_features) / len(frame_features)
    skin = sum(item.get("skin_likelihood", 0.0) for item in frame_features) / len(frame_features)
    motion_smoothness = sum(item.get("motion_smoothness", 0.5) for item in frame_features) / len(frame_features)

    if edge > 0.22 and saturation > 0.42 and texture < 0.28:
        return {"style": "anime_2d", "confidence": clamp01(0.55 + edge + saturation - texture), "reason": "high edge density, saturated colors, low texture"}
    if skin > 0.12 and texture > 0.25:
        return {"style": "live_action", "confidence": clamp01(0.55 + skin + texture * 0.5), "reason": "skin-like tones and natural texture"}
    if texture > 0.18 and motion_smoothness > 0.55 and saturation > 0.25:
        return {"style": "animation_3d", "confidence": clamp01(0.45 + motion_smoothness * 0.4), "reason": "smooth motion with rendered-looking texture"}
    if abs(edge - texture) < 0.08:
        return {"style": "mixed", "confidence": 0.45, "reason": "mixed visual statistics"}
    return {"style": "unknown", "confidence": 0.25, "reason": "weak style evidence"}
