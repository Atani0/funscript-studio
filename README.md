# Funscript Studio

**中文 | [English](#english)**

Funscript Studio 是一个本地优先的桌面端 funscript 编辑器与生成工具，面向视频播放、时间轴精修、感知层分析、混合生成、脚本导出和可选的 OSR2/SR6 设备预览调试。

当前版本：**0.1.0-alpha.1**

> 这是一个 Alpha / Preview 预发布版本，仍在快速迭代中。建议先在测试目录中解压运行。

## 中文

### 项目简介

Funscript Studio 使用 Electron + React + TypeScript 构建桌面 UI，并通过本地 Python 后端进行音频、视频、人体动作、互动强度和镜头感知分析。它的目标是把“视频 → 自动生成脚本 → 可视化编辑 → 导出 → 可选设备预览”整合到一个本地工具里。

项目默认本地运行，不会自动上传视频、脚本、训练数据或生成结果。

### 主要功能

- 本地视频导入与播放
- 专业曲线时间轴编辑器
- 播放头同步、缩放、拖动、节点编辑
- funscript 导入与导出
- 同目录同名脚本自动导入
- 多轴脚本基础支持：升降、前后、左右、旋转、侧倾、俯仰
- 快速节拍生成
- 感知层分析
- 混合生成 / Hybrid Generate
- 混合模式 +2、高能模式、节拍优先模式
- 训练集导入、参数拟合、相似片段匹配
- 质量评估指标
- 本地 Python 后端
- 可选 OSR2 / SR6 T-Code USB 串口输出
- 设备轴向限位保存与实时位置显示
- 窗口化 / 全屏静音预览镜像
- Windows 便携预览版打包

### 下载

请在 [Releases](https://github.com/Atani0/funscript-studio/releases) 页面下载：

- `FunscriptStudio-Portable-Windows-0.1.0-alpha.1.zip`：Windows 便携版，解压后运行。
- `FunscriptStudio-Source-0.1.0-alpha.1.zip`：用于代码审查、学习和二次开发的源码包。

### 架构概览

```text
Video + Audio
  -> Python Perception Engine
  -> Hybrid Generator / Learning Module
  -> React Timeline Editor
  -> Exported Funscript
  -> Optional local T-Code device bridge
```

主要目录：

- `electron/`：Electron 主进程和 preload 桥接
- `src/`：React + TypeScript 前端界面
- `backend/`：本地 Python HTTP 后端
- `backend/perception/`：感知层时间线生成
- `backend/generation/`：事件提取、运动规划、动作合成、质量评估
- `backend/learning/`：训练集、学习配置、相似片段索引
- `scripts/`：安装、启动、便携版打包脚本

### 安装与运行

推荐环境：

- Windows 10 / 11
- Node.js 18+
- pnpm
- Python 3.10+
- FFmpeg，或项目中的 `ffmpeg-static` 依赖

安装依赖：

```powershell
.\install.bat
```

启动预览版：

```powershell
.\start.bat
```

开发模式：

```powershell
pnpm install
pnpm run dev
```

运行检查：

```powershell
pnpm run typecheck
pnpm run build
python -m pytest tests
```

构建 Windows 便携预览包：

```powershell
.\build-preview.bat
```

输出文件会生成在 `outputs/` 目录下。

### 隐私说明

- 软件默认本地优先。
- 不会自动上传用户视频、funscript、训练集、感知层 JSON、学习配置或生成结果。
- 用户数据目录不应提交到 GitHub。
- 如果未来加入外部 API，用户必须手动配置并理解隐私风险。

### 设备控制安全说明

设备输出仍是实验功能，请谨慎使用。

- 连接实体设备前，请先设置轴向限位、振幅、速度和频率范围。
- 建议先用预览模式检查脚本。
- 项目不对外部设备或不安全限位造成的风险负责。
- 默认限位较保守，用户可以在设备调试面板中调整。

### 当前状态

状态：**Alpha**

已知限制：

- 自动生成脚本质量仍可能不稳定。
- 感知层对真人、3D 动画、2D 动画、剪辑视频的识别效果不同。
- 当前学习模块以参数拟合和相似片段匹配为主，尚未内置深度学习模型。
- 默认不包含示例视频、样本脚本或训练数据。
- 设备支持取决于系统串口、硬件和用户授权。
- 部分视频格式会通过 FFmpeg 转换为本地临时 MP4 预览。

路线图：

- 更好的感知层特征验证工具
- 更稳定的混合生成配置
- 更安全的设备模拟和校准流程
- 更清晰的插件 / 模型扩展接口
- 保持本地优先的前提下，预留未来深度模型接入能力

### 安全与贡献

- 安全说明请阅读 [SECURITY.md](SECURITY.md)
- 贡献指南请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)
- 许可证：MIT，见 [LICENSE](LICENSE)

---

## English

Funscript Studio is a local-first desktop funscript editor and generation tool for video playback, timeline editing, perception analysis, hybrid generation, script export, and optional OSR2/SR6 device preview/debugging.

Current version: **0.1.0-alpha.1**

> This is an Alpha / Preview pre-release. The project is still evolving quickly. Extract and run it in a test folder first.

### Overview

Funscript Studio combines an Electron + React + TypeScript desktop UI with a local Python backend for audio, video, body-motion, interaction, and shot-level perception analysis. The long-term goal is to provide a local workflow for “video → generated script → visual editing → export → optional device preview”.

The project is local-first by default. It does not automatically upload videos, scripts, training data, or generated outputs.

### Features

- Local video import and playback
- Professional curve timeline editor
- Playhead sync, zooming, scrubbing, keyframe editing
- Funscript import and export
- Same-name script auto-import from the video folder
- Basic multi-axis support: stroke, surge, sway, twist, roll, pitch
- Fast beat-based generation
- Perception analysis
- Hybrid Generate
- Hybrid +2, energetic mode, and beat-matched mode
- Training dataset import, parameter fitting, and similar-segment matching
- Quality metrics
- Local Python backend
- Optional OSR2 / SR6 T-Code USB serial output
- Persistent axis limits and live device-position visualization
- Windowed / fullscreen muted preview mirror
- Windows portable preview packaging

### Downloads

Download from the [Releases](https://github.com/Atani0/funscript-studio/releases) page:

- `FunscriptStudio-Portable-Windows-0.1.0-alpha.1.zip`: Windows portable build. Extract and run.
- `FunscriptStudio-Source-0.1.0-alpha.1.zip`: Clean source package for code review, learning, and further development.

### Architecture

```text
Video + Audio
  -> Python Perception Engine
  -> Hybrid Generator / Learning Module
  -> React Timeline Editor
  -> Exported Funscript
  -> Optional local T-Code device bridge
```

Main directories:

- `electron/`: Electron main process and preload bridge
- `src/`: React + TypeScript renderer UI
- `backend/`: local Python HTTP backend
- `backend/perception/`: perception timeline generation
- `backend/generation/`: event extraction, motion planning, action synthesis, and quality metrics
- `backend/learning/`: training datasets, learned profiles, and similarity index
- `scripts/`: install, start, and portable packaging helpers

### Installation and usage

Recommended environment:

- Windows 10 / 11
- Node.js 18+
- pnpm
- Python 3.10+
- FFmpeg, or the bundled `ffmpeg-static` dependency

Install dependencies:

```powershell
.\install.bat
```

Start preview build:

```powershell
.\start.bat
```

Development mode:

```powershell
pnpm install
pnpm run dev
```

Run checks:

```powershell
pnpm run typecheck
pnpm run build
python -m pytest tests
```

Build a Windows portable preview package:

```powershell
.\build-preview.bat
```

Build outputs are written under `outputs/`.

### Data privacy

- The software is local-first by default.
- It does not automatically upload user videos, funscripts, training datasets, perception JSON, learned profiles, or generated outputs.
- User data directories should not be committed to GitHub.
- If external API integrations are added in the future, users must configure them explicitly and understand the privacy risks.

### Device-control safety note

Device output is experimental and should be used carefully.

- Set axis limits, amplitude, speed, and frequency ranges before testing with physical devices.
- Verify scripts in preview mode first.
- The project is not responsible for risks caused by external devices or unsafe limits.
- Default limits are intentionally conservative and can be adjusted in the device panel.

### Development status

Status: **Alpha**

Known limitations:

- Generated script quality can still be unstable.
- Perception accuracy varies across live-action, 3D animation, 2D animation, and heavily edited videos.
- The current learning module uses parameter fitting and similar-segment matching rather than a built-in deep learning model.
- No default sample videos, sample scripts, or training datasets are included.
- Device support depends on serial availability, hardware, and user permission.
- Some media formats are converted to temporary local MP4 previews using FFmpeg.

Roadmap:

- Better perception feature validation tools
- More robust hybrid generation profiles
- Safer device simulation and calibration workflows
- Cleaner plugin / model extension points
- Future deep-model integration while keeping the local-first default

### Security and contributing

- Read [SECURITY.md](SECURITY.md) for security notes.
- Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening issues or pull requests.
- License: MIT. See [LICENSE](LICENSE).
