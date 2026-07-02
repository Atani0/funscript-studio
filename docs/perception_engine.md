# Funscript Studio 感知层 Perception Engine

本次升级把原来的 `audio RMS + frame diff` 拆成独立的多模态感知层。它不直接等于最终脚本，而是先输出结构化的 `perception timeline`，后续 `generator.py` / `motion_engine` 再根据这些特征生成 funscript。

## Pipeline

```text
Video
  → FrameSampler 流式抽帧
  → VisualAnalyzer / PoseAnalyzer / MultiPersonTracker / ShotAnalyzer / InteractionAnalyzer
  → AudioAnalyzer
  → FeatureFusion
  → perception.json
  → generator.generate_from_perception()
  → funscript
```

## 后端模块

- `backend/perception/perception_engine.py`：统一入口，负责调度抽帧、音频、视觉、姿态、互动和融合。
- `frame_sampler.py`：按 `fast / balanced / high_quality` 流式抽帧，默认 balanced 为 10 FPS，避免长视频一次性进内存。
- `visual_analyzer.py`：计算 frame diff、运动区域、边缘密度、颜色/纹理特征和 scene change。
- `style_classifier.py`：rule-based 判断 `live_action / anime_2d / animation_3d / mixed / unknown`，用于选择后续策略。
- `pose_analyzer.py`：优先使用 MediaPipe Pose；不可用或置信度低时自动回退到 optical-flow 伪姿态。
- `multi_person_tracker.py`：基于中心距离的轻量 track id 保持，后续可替换 ByteTrack / DeepSORT。
- `interaction_analyzer.py`：输出多人距离、靠近速度、同步动作、接触可能性和互动强度，不输出语义标签。
- `shot_analyzer.py`：根据人体框、运动区域和姿态可见性推断全身、上半身、特写、远景等镜头类型。
- `audio_analyzer.py`：支持 `music / event / auto`，输出 RMS、onset、beat/transient、clap/impact 倾向等节奏特征。
- `feature_fusion.py`：把音频、视觉、姿态、镜头、互动统一融合成 `segments`，并给出 `suggested_motion`。

## JSON Schema 摘要

```json
{
  "version": "1.0",
  "duration": 123000,
  "style": {
    "style": "live_action",
    "confidence": 0.74,
    "reason": "rule based visual features"
  },
  "summary": {
    "duration": 123000,
    "style": "live_action",
    "avgMotion": 0.62,
    "avgInteraction": 0.31,
    "audioMode": "music",
    "confidence": 0.74
  },
  "segments": [
    {
      "start": 12000,
      "end": 12500,
      "shot_type": "full_body",
      "confidence": 0.78,
      "visual": {
        "motion_intensity": 0.5,
        "body_motion_overall": 0.4,
        "upper_body_motion": 0.3,
        "lower_body_motion": 0.2,
        "hand_motion": 0.3,
        "leg_motion": 0.2,
        "hip_motion": 0.4,
        "torso_motion": 0.4,
        "scene_change": false
      },
      "interaction": {
        "person_count": 1,
        "interaction_intensity": 0.0,
        "proximity": 0.0,
        "sync_motion": 0.0,
        "contact_likelihood": 0.0
      },
      "audio": {
        "mode": "music",
        "beat_strength": 0.6,
        "onset_strength": 0.4,
        "transient_strength": 0.2,
        "clap_likelihood": 0.0,
        "tempo_confidence": 0.7
      },
      "suggested_motion": {
        "intensity": 0.55,
        "rhythm_density": 0.5,
        "smoothness": 0.65,
        "accent": 0.45
      },
      "explain": ["style=live_action strategy=pose-first"]
    }
  ]
}
```

## API

### POST `/api/perception/analyze`

输入：

```json
{
  "videoPath": "D:/video.mp4",
  "quality": "fast | balanced | high_quality",
  "audioMode": "auto | music | event",
  "visualMode": "auto | pose | optical_flow | hybrid",
  "saveDebugFrames": false
}
```

输出：

```json
{
  "ok": true,
  "id": "perception_xxx",
  "perceptionPath": "backend/perception_outputs/perception_xxx.json",
  "summary": {
    "duration": 123000,
    "style": "live_action",
    "avgMotion": 0.62,
    "avgInteraction": 0.31,
    "audioMode": "music",
    "confidence": 0.74
  }
}
```

### GET `/api/perception/:id`

返回当前后端进程缓存的 perception JSON。

### POST `/api/generate/from-perception`

输入：

```json
{
  "perceptionPath": "backend/perception_outputs/perception_xxx.json",
  "axis": "stroke",
  "profile": "balanced | smooth | energetic | beat_matched"
}
```

输出标准 funscript JSON。

## UI 调试方式

主界面新增：

- “分析感知层”：对当前视频生成 perception JSON。
- “感知生成”：从 perception timeline 生成当前轴脚本。
- “感知时间线”：显示视觉、姿态、互动、音频四条调试轨。
- “感知层调试”：查看当前时间点的融合、音频、视觉、互动和完整 JSON。
- “打开叠加”：在视频上显示镜头类型、风格、置信度、运动区域等信息。
- “导入/导出感知 JSON”：避免重复分析长视频。

## 被 generator 使用

`backend/generator.py` 新增 `generate_from_perception(perception_path, axis, profile)`。它读取 `segments[].suggested_motion`、音频节奏和视觉运动，生成 MultiFunPlayer 可识别的标准：

```json
{
  "version": "1.0",
  "actions": [{ "at": 1000, "pos": 50 }]
}
```

旧的 baseline 生成逻辑仍保留，感知层失败时不会破坏现有自动生成功能。

## 后续接入 DeepSeek / GPT Director Layer

感知层保持本地、隐私友好、可缓存。后续如果需要大模型，只建议放在 “director layer”：

1. 输入压缩后的 perception summary / segments，不上传原视频。
2. 让模型给出节奏策略、段落结构、轴分配建议。
3. 本地 generator 根据建议和 perception timeline 生成最终 funscript。

这样既避免把大模型强耦合进底层 CV，也能保留可解释、可调试、可回退的本地管线。
