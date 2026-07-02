# Hybrid Learned Generator

## 为什么要新增 Hybrid Generator

旧的快速生成在音乐强节奏视频上经常表现不错，因为它直接依赖 audio beat / onset / peak，动作点 timing 比较准。

旧的 perception 生成虽然读取了更多视觉信息，但它按固定 segment 反转方向，容易出现：

- 固定 22 / 78 / 22 / 78；
- 固定 250ms 一跳；
- 峰值和低谷长期不变；
- 感知数据只影响强度，没有真正影响 timing、密度、幅度和平滑度。

Hybrid Generator 的原则是：

```text
audio events 决定什么时候动
perception features 决定怎么动、强弱、密度、幅度、平滑度
training examples 学习用户偏好的风格
similar segments 参考优质片段的局部写法
```

## 新模块

### `/backend/generation`

- `event_candidate_extractor.py`：从 beat / onset / transient / body peak / interaction / scene change 提取候选动作点。
- `motion_planner.py`：把候选事件变成动作计划，计算强度、幅度、方向和平滑度。
- `action_synthesizer.py`：把 motion plan 转成 funscript actions，避免固定高低值和固定间隔。
- `quality_metrics.py`：检测动作数量、平均间隔、幅度变化、beat 对齐率、机械重复和固定峰谷。

### `/backend/learning`

- `training_dataset.py`：训练集 JSON 的创建、添加、删除和目录扫描。
- `script_feature_extractor.py`：从优质 funscript 提取密度、幅度、速度、平滑度和重复度。
- `perception_aligner.py`：按 1s / 2s / 4s 窗口对齐 perception 和 funscript。
- `parameter_fitter.py`：从训练样本拟合 learned_profile。
- `similarity_index.py`：纯 Python 相似片段索引，支持 cosine similarity 和 top_k 查询。
- `learned_profile.py`：默认 profile、加载和保存。
- `hybrid_generator.py`：高层 Hybrid / Learned Hybrid 生成入口。
- `deep_model_interface.py`：后续深度模型接口，不参与当前运行。

## API

### POST `/api/generate/hybrid`

输入：

```json
{
  "videoPath": "D:/video.mp4",
  "perceptionPath": "backend/perception_outputs/perception_xxx.json",
  "profilePath": "data/training_datasets/my_style/learned_profile.json",
  "datasetName": "my_style",
  "mode": "hybrid",
  "style": "balanced",
  "axis": "stroke"
}
```

输出：

```json
{
  "ok": true,
  "funscript": {
    "version": "1.0",
    "actions": [{ "at": 0, "pos": 50 }]
  },
  "summary": {
    "actionCount": 430,
    "avgIntervalMs": 260,
    "amplitudeVariance": 0.31,
    "beatAlignmentRate": 0.84,
    "usedLearnedProfile": true,
    "usedSimilarSegments": true
  }
}
```

如果 profile 或 similarity index 不存在，会自动使用默认参数；如果 Hybrid 失败，会 fallback 到旧快速生成。

## learned_profile.json

保存训练出来的用户风格偏好：

- `weights`：音频、视觉、身体动作、互动、镜头切换权重；
- `timing`：最小动作间隔、偏好间隔、beat snap 容忍；
- `amplitude`：位置范围、中心点、偏好幅度、变化量；
- `density`：低运动/高运动密度；
- `smoothness`：平滑参数和避免机械重复策略；
- `style_bias`：beat matched、energetic、pose aware 等风格倾向。

## similarity_index.json

保存训练集切片：

- perception feature vector；
- 对应脚本片段统计；
- 相对 actions；
- shot type / style / metadata。

第一版使用纯 Python cosine similarity，后续可替换 FAISS。

## 前端入口

主界面新增 `Hybrid 生成器` 面板：

- `Hybrid Generate`：默认推荐；
- `Beat Matched`：更保留快速生成的节奏优势；
- `Energetic`：保留更多事件、更高密度；
- `Learned Hybrid`：如果已有训练 profile / similarity index，则会使用它们。

生成后会显示 quality summary 和相似片段结果。

## 质量指标

`quality_metrics.py` 输出：

- `action_count`
- `avg_interval_ms`
- `interval_variance`
- `amplitude_variance`
- `beat_alignment_rate`
- `mechanical_repetition_score`
- `fixed_peak_valley_score`
- `smoothness`
- `warnings`

重点用于发现：

- 长期固定 20/80 交替；
- 动作点过于固定间隔；
- beat 对齐率太低；
- 幅度变化太小。

## 后续深度模型

`deep_model_interface.py` 预留：

- action_probability_model；
- amplitude_regression_model；
- density_prediction_model；
- style_embedding_model。

当前版本不依赖任何 API，也不依赖深度模型。未来可以把 Hybrid Generator 里的部分规则替换为本地模型预测。
