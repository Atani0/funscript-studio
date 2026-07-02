# Funscript Studio

**涓枃 | [English](#english)**

Funscript Studio 鏄竴涓湰鍦颁紭鍏堢殑妗岄潰绔?funscript 缂栬緫鍣ㄤ笌鐢熸垚宸ュ叿锛岄潰鍚戣棰戞挱鏀俱€佹椂闂磋酱绮句慨銆佹劅鐭ュ眰鍒嗘瀽銆佹贩鍚堢敓鎴愩€佽剼鏈鍑哄拰鍙€夌殑 OSR2/SR6 璁惧棰勮璋冭瘯銆?
褰撳墠鐗堟湰锛?*0.1.0-alpha.1**

> 杩欐槸涓€涓?Alpha / Preview 棰勫彂甯冪増鏈紝浠嶅湪蹇€熻凯浠ｄ腑銆傚缓璁厛鍦ㄦ祴璇曠洰褰曚腑瑙ｅ帇杩愯銆?
## 涓枃

### 椤圭洰绠€浠?
Funscript Studio 浣跨敤 Electron + React + TypeScript 鏋勫缓妗岄潰 UI锛屽苟閫氳繃鏈湴 Python 鍚庣杩涜闊抽銆佽棰戙€佷汉浣撳姩浣溿€佷簰鍔ㄥ己搴﹀拰闀滃ご鎰熺煡鍒嗘瀽銆傚畠鐨勭洰鏍囨槸鎶娾€滆棰?鈫?鑷姩鐢熸垚鑴氭湰 鈫?鍙鍖栫紪杈?鈫?瀵煎嚭 鈫?鍙€夎澶囬瑙堚€濇暣鍚堝埌涓€涓湰鍦板伐鍏烽噷銆?
椤圭洰榛樿鏈湴杩愯锛屼笉浼氳嚜鍔ㄤ笂浼犺棰戙€佽剼鏈€佽缁冩暟鎹垨鐢熸垚缁撴灉銆?
### 涓昏鍔熻兘

- 鏈湴瑙嗛瀵煎叆涓庢挱鏀?- 涓撲笟鏇茬嚎鏃堕棿杞寸紪杈戝櫒
- 鎾斁澶村悓姝ャ€佺缉鏀俱€佹嫋鍔ㄣ€佽妭鐐圭紪杈?- funscript 瀵煎叆涓庡鍑?- 鍚岀洰褰曞悓鍚嶈剼鏈嚜鍔ㄥ鍏?- 澶氳酱鑴氭湰鍩虹鏀寔锛氬崌闄嶃€佸墠鍚庛€佸乏鍙炽€佹棆杞€佷晶鍊俱€佷刊浠?- 蹇€熻妭鎷嶇敓鎴?- 鎰熺煡灞傚垎鏋?- 娣峰悎鐢熸垚 / Hybrid Generate
- 娣峰悎妯″紡 +2銆侀珮鑳芥ā寮忋€佽妭鎷嶄紭鍏堟ā寮?- 璁粌闆嗗鍏ャ€佸弬鏁版嫙鍚堛€佺浉浼肩墖娈靛尮閰?- 璐ㄩ噺璇勪及鎸囨爣
- 鏈湴 Python 鍚庣
- 鍙€?OSR2 / SR6 T-Code USB 涓插彛杈撳嚭
- 璁惧杞村悜闄愪綅淇濆瓨涓庡疄鏃朵綅缃樉绀?- 绐楀彛鍖?/ 鍏ㄥ睆闈欓煶棰勮闀滃儚
- Windows 渚挎惡棰勮鐗堟墦鍖?
### 涓嬭浇

璇峰湪 [Releases](https://github.com/Atani0/funscript-studio/releases) 椤甸潰涓嬭浇锛?
- `FunscriptStudio-Portable-Windows-0.1.0-alpha.1.zip`锛歐indows 渚挎惡鐗堬紝瑙ｅ帇鍚庤繍琛屻€?- `FunscriptStudio-Source-0.1.0-alpha.1.zip`锛氱敤浜庝唬鐮佸鏌ャ€佸涔犲拰浜屾寮€鍙戠殑婧愮爜鍖呫€?
### 鏋舵瀯姒傝

```text
Video + Audio
  -> Python Perception Engine
  -> Hybrid Generator / Learning Module
  -> React Timeline Editor
  -> Exported Funscript
  -> Optional local T-Code device bridge
```

涓昏鐩綍锛?
- `electron/`锛欵lectron 涓昏繘绋嬪拰 preload 妗ユ帴
- `src/`锛歊eact + TypeScript 鍓嶇鐣岄潰
- `backend/`锛氭湰鍦?Python HTTP 鍚庣
- `backend/perception/`锛氭劅鐭ュ眰鏃堕棿绾跨敓鎴?- `backend/generation/`锛氫簨浠舵彁鍙栥€佽繍鍔ㄨ鍒掋€佸姩浣滃悎鎴愩€佽川閲忚瘎浼?- `backend/learning/`锛氳缁冮泦銆佸涔犻厤缃€佺浉浼肩墖娈电储寮?- `scripts/`锛氬畨瑁呫€佸惎鍔ㄣ€佷究鎼虹増鎵撳寘鑴氭湰

### 瀹夎涓庤繍琛?
鎺ㄨ崘鐜锛?
- Windows 10 / 11
- Node.js 18+
- pnpm
- Python 3.10+
- FFmpeg锛屾垨椤圭洰涓殑 `ffmpeg-static` 渚濊禆

瀹夎渚濊禆锛?
```powershell
.\install.bat
```

鍚姩棰勮鐗堬細

```powershell
.\start.bat
```

寮€鍙戞ā寮忥細

```powershell
pnpm install
pnpm run dev
```

杩愯妫€鏌ワ細

```powershell
pnpm run typecheck
pnpm run build
python -m pytest tests
```

鏋勫缓 Windows 渚挎惡棰勮鍖咃細

```powershell
.\build-preview.bat
```

杈撳嚭鏂囦欢浼氱敓鎴愬湪 `outputs/` 鐩綍涓嬨€?
### 闅愮璇存槑

- 杞欢榛樿鏈湴浼樺厛銆?- 涓嶄細鑷姩涓婁紶鐢ㄦ埛瑙嗛銆乫unscript銆佽缁冮泦銆佹劅鐭ュ眰 JSON銆佸涔犻厤缃垨鐢熸垚缁撴灉銆?- 鐢ㄦ埛鏁版嵁鐩綍涓嶅簲鎻愪氦鍒?GitHub銆?- 濡傛灉鏈潵鍔犲叆澶栭儴 API锛岀敤鎴峰繀椤绘墜鍔ㄩ厤缃苟鐞嗚В闅愮椋庨櫓銆?
### 璁惧鎺у埗瀹夊叏璇存槑

璁惧杈撳嚭浠嶆槸瀹為獙鍔熻兘锛岃璋ㄦ厧浣跨敤銆?
- 杩炴帴瀹炰綋璁惧鍓嶏紝璇峰厛璁剧疆杞村悜闄愪綅銆佹尟骞呫€侀€熷害鍜岄鐜囪寖鍥淬€?- 寤鸿鍏堢敤棰勮妯″紡妫€鏌ヨ剼鏈€?- 椤圭洰涓嶅澶栭儴璁惧鎴栦笉瀹夊叏闄愪綅閫犳垚鐨勯闄╄礋璐ｃ€?- 榛樿闄愪綅杈冧繚瀹堬紝鐢ㄦ埛鍙互鍦ㄨ澶囪皟璇曢潰鏉夸腑璋冩暣銆?
### 褰撳墠鐘舵€?
鐘舵€侊細**Alpha**

宸茬煡闄愬埗锛?
- 鑷姩鐢熸垚鑴氭湰璐ㄩ噺浠嶅彲鑳戒笉绋冲畾銆?- 鎰熺煡灞傚鐪熶汉銆?D 鍔ㄧ敾銆?D 鍔ㄧ敾銆佸壀杈戣棰戠殑璇嗗埆鏁堟灉涓嶅悓銆?- 褰撳墠瀛︿範妯″潡浠ュ弬鏁版嫙鍚堝拰鐩镐技鐗囨鍖归厤涓轰富锛屽皻鏈唴缃繁搴﹀涔犳ā鍨嬨€?- 榛樿涓嶅寘鍚ず渚嬭棰戙€佹牱鏈剼鏈垨璁粌鏁版嵁銆?- 璁惧鏀寔鍙栧喅浜庣郴缁熶覆鍙ｃ€佺‖浠跺拰鐢ㄦ埛鎺堟潈銆?- 閮ㄥ垎瑙嗛鏍煎紡浼氶€氳繃 FFmpeg 杞崲涓烘湰鍦颁复鏃?MP4 棰勮銆?
璺嚎鍥撅細

- 鏇村ソ鐨勬劅鐭ュ眰鐗瑰緛楠岃瘉宸ュ叿
- 鏇寸ǔ瀹氱殑娣峰悎鐢熸垚閰嶇疆
- 鏇村畨鍏ㄧ殑璁惧妯℃嫙鍜屾牎鍑嗘祦绋?- 鏇存竻鏅扮殑鎻掍欢 / 妯″瀷鎵╁睍鎺ュ彛
- 淇濇寔鏈湴浼樺厛鐨勫墠鎻愪笅锛岄鐣欐湭鏉ユ繁搴︽ā鍨嬫帴鍏ヨ兘鍔?
### 瀹夊叏涓庤础鐚?
- 瀹夊叏璇存槑璇烽槄璇?[SECURITY.md](SECURITY.md)
- 璐＄尞鎸囧崡璇烽槄璇?[CONTRIBUTING.md](CONTRIBUTING.md)
- 璁稿彲璇侊細MIT锛岃 [LICENSE](LICENSE)

---

## English

Funscript Studio is a local-first desktop funscript editor and generation tool for video playback, timeline editing, perception analysis, hybrid generation, script export, and optional OSR2/SR6 device preview/debugging.

Current version: **0.1.0-alpha.1**

> This is an Alpha / Preview pre-release. The project is still evolving quickly. Extract and run it in a test folder first.

### Overview

Funscript Studio combines an Electron + React + TypeScript desktop UI with a local Python backend for audio, video, body-motion, interaction, and shot-level perception analysis. The long-term goal is to provide a local workflow for 鈥渧ideo 鈫?generated script 鈫?visual editing 鈫?export 鈫?optional device preview鈥?

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
