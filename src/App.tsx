import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { generateFromBackend } from './app/generation_service';
import {
  applyCurveMode,
  commitTimeline,
  createTimelineHistory,
  redoTimeline,
  replaceTimeline,
  undoTimeline,
  type TimelineHistory,
} from './app/timeline_controller';
import { formatTime } from './app/video_controller';
import { axes, createAxisScripts, inferAxisFromFunscriptName, updateAxisScript } from './core/axis_manager';
import { sanitizeActions } from './core/funscript_model';
import { parseFunscript, serializeFunscript } from './core/funscript_parser';
import { smoothActions } from './core/motion_model';
import type { PerceptionAnalyzeResult, PerceptionTimeline as PerceptionTimelineData } from './core/perceptionTypes';
import type { AxisName, AxisScripts, CurveMode, FunscriptAction, VideoSource } from './core/types';
import { PerceptionDebugPanel } from './perception/PerceptionDebugPanel';
import { PerceptionOverlay } from './perception/PerceptionOverlay';
import { PerceptionTimeline } from './perception/PerceptionTimeline';
import { HybridGeneratePanel } from './learning/HybridGeneratePanel';
import { SimilarSegmentsPanel } from './learning/SimilarSegmentsPanel';
import { AxisPanel } from './ui/AxisPanel';
import { DevicePanel } from './ui/DevicePanel';
import { ScriptEditor } from './ui/ScriptEditor';
import { TimelineEditor } from './ui/TimelineEditor';
import { VideoPlayer, type VideoPlayerHandle } from './ui/VideoPlayer';

const createHistories = (): Record<AxisName, TimelineHistory> =>
  Object.fromEntries(axes.map(name => [name, createTimelineHistory()])) as Record<AxisName, TimelineHistory>;

const createAxisFlags = (value = false): Record<AxisName, boolean> =>
  Object.fromEntries(axes.map(name => [name, value])) as Record<AxisName, boolean>;

type PersistedState = {
  axis?: AxisName;
  zoom?: number;
  timelineViewStart?: number;
  curveMode?: CurveMode;
  locked?: Record<AxisName, boolean>;
  batchMode?: string;
};

type BatchPreset = { mode: string; style: string; label: string };
type PlaybackMode = 'single' | 'folder';
type PreviewMenu = { x: number; y: number } | null;
type PreviewControl = { type?: 'play' | 'pause' | 'toggle' | 'seek' | 'importVideo'; timeMs?: number; videoPath?: string };

const batchPresets: Record<string, BatchPreset> = {
  hybrid: { mode: 'hybrid', style: 'balanced', label: '混合模式' },
  hybrid_plus2: { mode: 'hybrid_plus2', style: 'balanced', label: '混合模式+2' },
  energetic: { mode: 'hybrid', style: 'energetic', label: '高能模式' },
  beat_matched: { mode: 'hybrid', style: 'beat_matched', label: '节拍优先模式' },
};

const safeDuration = (durationMs: unknown, fallback = 10_000) =>
  typeof durationMs === 'number' && Number.isFinite(durationMs) && durationMs > 0 ? durationMs : fallback;

const clampTime = (timeMs: number, durationMs: number) =>
  Math.max(0, Math.min(safeDuration(durationMs, 1), Number.isFinite(timeMs) ? timeMs : 0));

const cloneActions = (actions: FunscriptAction[]) => actions.map(action => ({ ...action }));

const intensifyActions = (actions: FunscriptAction[], factor = 1.28): FunscriptAction[] =>
  actions.map(action => ({
    ...action,
    pos: Math.max(0, Math.min(100, Math.round(50 + (action.pos - 50) * factor))),
  }));

export default function App() {
  const videoRef = useRef<VideoPlayerHandle>(null);
  const playerCardRef = useRef<HTMLDivElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const scriptInputRef = useRef<HTMLInputElement>(null);
  const perceptionInputRef = useRef<HTMLInputElement>(null);
  const restoredRef = useRef(false);
  const previewStateRef = useRef<Record<string, unknown> | null>(null);

  const [video, setVideo] = useState<VideoSource>();
  const [scripts, setScripts] = useState<AxisScripts>(createAxisScripts);
  const [histories, setHistories] = useState<Record<AxisName, TimelineHistory>>(createHistories);
  const [axis, setAxis] = useState<AxisName>('stroke');
  const [locked, setLocked] = useState<Record<AxisName, boolean>>(() => createAxisFlags(false));
  const [curveMode, setCurveMode] = useState<CurveMode>('smooth');
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>('single');
  const [folderVideos, setFolderVideos] = useState<string[]>([]);
  const [previewMenu, setPreviewMenu] = useState<PreviewMenu>(null);
  const [zoom, setZoom] = useState(1);
  const [timelineViewStart, setTimelineViewStart] = useState(0);
  const [batchMode, setBatchMode] = useState('hybrid');
  const [analyzing, setAnalyzing] = useState(false);
  const [perceptionAnalyzing, setPerceptionAnalyzing] = useState(false);
  const [perception, setPerception] = useState<PerceptionTimelineData | null>(null);
  const [hybridSummary, setHybridSummary] = useState<Record<string, unknown> | null>(null);
  const [similarSegments, setSimilarSegments] = useState<unknown[]>([]);
  const [overlayEnabled, setOverlayEnabled] = useState(false);
  const [previewSize, setPreviewSize] = useState({ width: 0, height: 410 });
  const [status, setStatus] = useState('准备就绪');

  const currentScript = scripts[axis];
  const currentHistory = histories[axis];
  const effectiveDurationMs = safeDuration(video?.durationMs, Math.max(10_000, currentScript.actions.at(-1)?.at ?? 10_000));

  useEffect(() => () => {
    if (video?.url?.startsWith('blob:')) URL.revokeObjectURL(video.url);
  }, [video?.url]);

  useEffect(() => {
    void window.desktopAPI.loadAppState().then(raw => {
      const state = raw as PersistedState | null;
      if (restoredRef.current) return;
      restoredRef.current = true;
      if (state?.axis) setAxis(state.axis);
      if (typeof state?.zoom === 'number' && Number.isFinite(state.zoom)) setZoom(state.zoom);
      if (typeof state?.timelineViewStart === 'number' && Number.isFinite(state.timelineViewStart)) setTimelineViewStart(state.timelineViewStart);
      if (state?.curveMode) setCurveMode(state.curveMode);
      if (state?.locked) setLocked(state.locked);
      if (state?.batchMode && batchPresets[state.batchMode]) setBatchMode(state.batchMode);
      setScripts(createAxisScripts());
      setHistories(createHistories());
      setPerception(null);
      setStatus('已打开空白项目');
    });
  }, []);

  useEffect(() => {
    if (!restoredRef.current) return;
    const timer = window.setTimeout(() => {
      void window.desktopAPI.saveAppState({ axis, zoom, timelineViewStart, curveMode, locked, batchMode });
    }, 500);
    return () => window.clearTimeout(timer);
  }, [axis, zoom, timelineViewStart, curveMode, locked, batchMode]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      const key = event.key.toLowerCase();
      if (event.code === 'Space') {
        event.preventDefault();
        videoRef.current?.toggle();
      }
      if (event.code === 'ArrowLeft') videoRef.current?.step(event.shiftKey ? -10 : -1);
      if (event.code === 'ArrowRight') videoRef.current?.step(event.shiftKey ? 10 : 1);
      if ((event.ctrlKey || event.metaKey) && key === 'z') {
        event.preventDefault();
        undo();
      }
      if ((event.ctrlKey || event.metaKey) && (key === 'y' || (event.shiftKey && key === 'z'))) {
        event.preventDefault();
        redo();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const counts = useMemo(() =>
    Object.fromEntries(axes.map(name => [name, scripts[name].actions.length])) as Record<AxisName, number>,
  [scripts]);

  const updateScriptsForAxis = (targetAxis: AxisName, actions: FunscriptAction[], baseScripts = scripts) => {
    let next = updateAxisScript(baseScripts, targetAxis, { ...baseScripts[targetAxis], actions });
    if (targetAxis === 'stroke') {
      for (const item of axes) {
        if (item !== 'stroke' && locked[item]) next = updateAxisScript(next, item, { ...next[item], actions: cloneActions(actions) });
      }
    }
    return next;
  };

  const applyActions = (nextActions: FunscriptAction[], commit: boolean) => {
    const sanitized = sanitizeActions(nextActions, effectiveDurationMs);
    setScripts(previous => updateScriptsForAxis(axis, sanitized, previous));
    setHistories(previous => ({
      ...previous,
      [axis]: commit ? commitTimeline(previous[axis], sanitized) : replaceTimeline(previous[axis], sanitized),
    }));
  };

  const undo = () => {
    setHistories(previous => {
      const nextHistory = undoTimeline(previous[axis]);
      setScripts(current => updateAxisScript(current, axis, { ...current[axis], actions: nextHistory.present }));
      return { ...previous, [axis]: nextHistory };
    });
  };

  const redo = () => {
    setHistories(previous => {
      const nextHistory = redoTimeline(previous[axis]);
      setScripts(current => updateAxisScript(current, axis, { ...current[axis], actions: nextHistory.present }));
      return { ...previous, [axis]: nextHistory };
    });
  };

  const openVideoPicker = () => videoInputRef.current?.click();

  const startPreviewResize = (mode: 'right' | 'bottom' | 'corner', event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const parentWidth = playerCardRef.current?.parentElement?.getBoundingClientRect().width ?? 1400;
    const currentWidth = previewSize.width || playerCardRef.current?.getBoundingClientRect().width || parentWidth;
    const currentHeight = previewSize.height;
    const startX = event.clientX;
    const startY = event.clientY;
    const onMove = (moveEvent: PointerEvent) => {
      const nextWidth = mode === 'bottom'
        ? currentWidth
        : Math.max(420, Math.min(parentWidth, currentWidth + moveEvent.clientX - startX));
      const nextHeight = mode === 'right'
        ? currentHeight
        : Math.max(240, Math.min(920, currentHeight + moveEvent.clientY - startY));
      setPreviewSize({ width: nextWidth, height: nextHeight });
    };
    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      document.body.classList.remove('resizing-preview');
    };
    document.body.classList.add('resizing-preview');
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };

  const fitPreviewToVideo = (width: number, height: number) => {
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
    const parentWidth = playerCardRef.current?.parentElement?.getBoundingClientRect().width ?? 1400;
    const currentWidth = previewSize.width || playerCardRef.current?.getBoundingClientRect().width || parentWidth;
    const aspect = height / width;
    if (aspect <= 1.05) return;
    const targetHeight = Math.round(Math.min(920, Math.max(560, currentWidth * Math.min(aspect, 1.35))));
    setPreviewSize(previous => ({
      ...previous,
      height: Math.max(previous.height, targetHeight),
    }));
  };

  const loadSiblingScriptsForVideo = async (videoPath: string) => {
    try {
      const siblingScripts = await window.desktopAPI.loadSiblingScripts(videoPath);
      if (!siblingScripts.length) return;
      const nextScripts = { ...createAxisScripts() };
      const nextHistories = createHistories();
      let firstAxis: AxisName | null = null;
      for (const script of siblingScripts) {
        const parsed = parseFunscript(script.content);
        const targetAxis = inferAxisFromFunscriptName(script.name);
        nextScripts[targetAxis] = parsed;
        nextHistories[targetAxis] = createTimelineHistory(parsed.actions);
        firstAxis ??= targetAxis;
      }
      setScripts(nextScripts);
      setHistories(nextHistories);
      if (firstAxis) setAxis(firstAxis);
      setStatus(`已载入视频，并自动导入同名脚本 ${siblingScripts.length} 个`);
    } catch (error) {
      setStatus(error instanceof Error ? `视频已载入，但同名脚本导入失败：${error.message}` : '视频已载入，但同名脚本导入失败');
    }
  };

  const refreshFolderVideos = async (videoPath: string) => {
    try {
      setFolderVideos(await window.desktopAPI.listSiblingVideos(videoPath));
    } catch {
      setFolderVideos([]);
    }
  };

  const setLoadedVideo = (source: VideoSource, resetScripts = true) => {
    if (video?.url?.startsWith('blob:')) URL.revokeObjectURL(video.url);
    setVideo(source);
    setCurrentTimeMs(0);
    setTimelineViewStart(0);
    setPlaying(false);
    setPerception(null);
    if (resetScripts) {
      setScripts(createAxisScripts());
      setHistories(createHistories());
    }
    setStatus(`已载入视频：${source.name}`);
    void refreshFolderVideos(source.path);
    void loadSiblingScriptsForVideo(source.path);
  };

  const importVideo = (file: File) => {
    const filePath = window.desktopAPI.getPathForFile(file);
    if (filePath) {
      void openVideoPath(filePath);
      return;
    }
    setLoadedVideo({
      name: file.name,
      path: filePath,
      url: URL.createObjectURL(file),
      durationMs: 0,
    });
  };

  const openVideoPath = async (videoPath: string) => {
    setStatus(`正在准备视频预览：${videoPath}`);
    const info = await window.desktopAPI.getVideoFileInfo(videoPath);
    setLoadedVideo({ ...info, durationMs: 0 });
    if (info.converted) setStatus(`已载入视频：${info.name} · 已生成临时 MP4 预览`);
  };

  const importScripts = async (files: File[]) => {
    if (!files.length) return;
    const imported: string[] = [];
    const failed: string[] = [];
    const nextScripts = { ...scripts };
    const nextHistories = { ...histories };
    let firstAxis: AxisName | null = null;

    for (const file of files) {
      try {
        const parsed = parseFunscript(await file.text());
        const targetAxis = inferAxisFromFunscriptName(file.name);
        nextScripts[targetAxis] = parsed;
        nextHistories[targetAxis] = createTimelineHistory(parsed.actions);
        firstAxis ??= targetAxis;
        imported.push(`${file.name} 鈫?${targetAxis}`);
      } catch {
        failed.push(file.name);
      }
    }

    if (imported.length) {
      setScripts(nextScripts);
      setHistories(nextHistories);
      if (firstAxis) setAxis(firstAxis);
    }
    setStatus([
      imported.length ? `已导入 ${imported.length} 个脚本：${imported.join('，')}` : '',
      failed.length ? `失败：${failed.join('，')}` : '',
    ].filter(Boolean).join('；') || '脚本导入失败');
  };

  const importScript = async (file: File) => {
    try {
      const parsed = parseFunscript(await file.text());
      const targetAxis = inferAxisFromFunscriptName(file.name);
      setScripts(previous => updateAxisScript(previous, targetAxis, parsed));
      setHistories(previous => ({ ...previous, [targetAxis]: createTimelineHistory(parsed.actions) }));
      setAxis(targetAxis);
      setStatus(`已导入脚本：${file.name} → ${targetAxis}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '导入失败');
    }
  };

  const generate = async () => {
    if (!video?.path || !safeDuration(video.durationMs, 0)) return;
    setAnalyzing(true);
    setStatus('正在运行事件驱动生成引擎...');
    try {
      const generated = await generateFromBackend(video.path, safeDuration(video.durationMs));
      setScripts(previous => updateAxisScript(previous, 'stroke', generated));
      setHistories(previous => ({ ...previous, stroke: createTimelineHistory(generated.actions) }));
      setAxis('stroke');
      setStatus(`生成完成：${generated.actions.length} 个动作 · ${generated.meta?.engine ?? '事件引擎'}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '自动生成失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const analyzePerception = async () => {
    if (!video?.path) {
      setStatus('请先导入视频');
      return;
    }
    setPerceptionAnalyzing(true);
    setStatus('正在分析感知层：音频、画面、姿态、镜头与互动...');
    try {
      const result: PerceptionAnalyzeResult = await window.desktopAPI.analyzePerception({
        videoPath: video.path,
        quality: 'balanced',
        audioMode: 'auto',
        visualMode: 'auto',
        saveDebugFrames: false,
      });
      const loaded = await window.desktopAPI.loadPerceptionFile(result.perceptionPath) as PerceptionTimelineData;
      setPerception({ ...loaded, id: result.id, perceptionPath: result.perceptionPath });
      setOverlayEnabled(true);
      setStatus(`感知分析完成：${result.summary.style} · 平均运动 ${result.summary.avgMotion.toFixed(2)} · 置信度 ${result.summary.confidence.toFixed(2)}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '感知分析失败');
    } finally {
      setPerceptionAnalyzing(false);
    }
  };

  const importPerception = async (file: File) => {
    try {
      const path = window.desktopAPI.getPathForFile(file);
      const loaded = await window.desktopAPI.loadPerceptionFile(path) as PerceptionTimelineData;
      setPerception({ ...loaded, perceptionPath: path });
      setOverlayEnabled(true);
      setStatus(`已导入感知数据：${file.name}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '感知数据导入失败');
    }
  };

  const exportPerception = async () => {
    if (!perception) return;
    const result = await window.desktopAPI.savePerceptionFile(perception);
    setStatus(result.canceled ? '已取消导出感知数据' : `已导出感知数据：${result.file}`);
  };

  const generateFromPerception = async () => {
    if (!perception?.perceptionPath) {
      setStatus('请先分析或导入包含 perceptionPath 的感知数据');
      return;
    }
    setAnalyzing(true);
    setStatus('正在根据感知时间线生成脚本...');
    try {
      const generated = await window.desktopAPI.generateFromPerception({
        perceptionPath: perception.perceptionPath,
        axis,
        profile: 'balanced',
      });
      setScripts(previous => updateAxisScript(previous, axis, generated));
      setHistories(previous => ({ ...previous, [axis]: createTimelineHistory(generated.actions) }));
      setStatus(`感知生成完成：${generated.actions.length} 个动作 → ${axis}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '感知生成失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const generateHybrid = async ({ mode, style }: { mode: string; style: string; useLearned: boolean; useSimilar: boolean }) => {
    if (!video?.path) {
      setStatus('请先导入视频');
      return;
    }
    setAnalyzing(true);
    setStatus(mode === 'learned_hybrid' ? '正在使用学习混合生成...' : '正在使用混合生成...');
    try {
      const result = await window.desktopAPI.generateHybrid({
        videoPath: video.path,
        perceptionPath: perception?.perceptionPath ?? '',
        mode,
        style,
        axis,
      });
      const generated = result.funscript;
      setScripts(previous => updateAxisScript(previous, axis, generated));
      setHistories(previous => ({ ...previous, [axis]: createTimelineHistory(generated.actions) }));
      setHybridSummary(result.summary);
      const meta = generated.meta as Record<string, unknown> | undefined;
      setSimilarSegments(Array.isArray(meta?.similarSegments) ? meta.similarSegments : []);
      setStatus(`混合生成完成：${generated.actions.length} 个动作`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '混合生成失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const exportAll = async () => {
    if (!video?.path) {
      setStatus('请先导入视频，脚本会导出到视频所在文件夹');
      return;
    }
    const payload = {
      baseName: video.name,
      videoPath: video.path,
      scripts: Object.fromEntries(axes.map(name => [name, serializeFunscript(scripts[name])])),
    };
    const result = await window.desktopAPI.exportScripts(payload);
    setStatus(result.canceled ? '已取消导出' : `已导出脚本：${result.file ?? result.directory}`);
  };

  const batchGenerate = async () => {
    const preset = batchPresets[batchMode] ?? batchPresets.hybrid;
    if (!preset) {
      setStatus('批量生成已取消：模式无效');
      return;
    }
    setAnalyzing(true);
    setStatus(`正在打开文件夹选择器：${preset.label}`);
    try {
      const result = await window.desktopAPI.batchGenerateScripts(preset);
      if (result.canceled) {
        setStatus('已取消批量生成');
      } else {
        setStatus(`批量生成完成：成功 ${result.successCount ?? 0} 个，失败 ${result.failedCount ?? 0} 个 · ${result.directory ?? ''}`);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '批量生成失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const applyMode = (mode: CurveMode) => {
    setCurveMode(mode);
    applyActions(applyCurveMode(currentScript.actions, mode), true);
  };

  const seek = (ms: number) => {
    const next = clampTime(ms, effectiveDurationMs);
    setCurrentTimeMs(next);
    videoRef.current?.seek(next);
  };

  useEffect(() => {
    previewStateRef.current = video ? {
      videoPath: video.path,
      videoUrl: video.url,
      currentTimeMs,
      durationMs: effectiveDurationMs,
      playing,
    } : null;
  }, [video, currentTimeMs, effectiveDurationMs, playing]);

  useEffect(() => {
    const dispose = window.desktopAPI.onPreviewControl((payload: Record<string, unknown>) => {
      const control = payload as PreviewControl;
      if (control.type === 'seek' && typeof control.timeMs === 'number') {
        seek(control.timeMs);
        return;
      }
      if (control.type === 'importVideo' && typeof control.videoPath === 'string') {
        void openVideoPath(control.videoPath).then(() => {
          setStatus('已从预览窗口拖拽导入视频，并自动检查同名脚本');
        }).catch(error => {
          setStatus(error instanceof Error ? `预览窗口导入失败：${error.message}` : '预览窗口导入失败');
        });
        return;
      }
      if (control.type === 'play') {
        setPlaying(true);
        videoRef.current?.play();
        return;
      }
      if (control.type === 'pause') {
        setPlaying(false);
        videoRef.current?.pause();
        return;
      }
      if (control.type === 'toggle') {
        videoRef.current?.toggle();
      }
    });
    return dispose;
  });

  useEffect(() => {
    let frame = 0;
    const pushPreviewState = () => {
      if (previewStateRef.current) window.desktopAPI.sendPreviewState(previewStateRef.current);
      frame = requestAnimationFrame(pushPreviewState);
    };
    frame = requestAnimationFrame(pushPreviewState);
    return () => cancelAnimationFrame(frame);
  }, []);

  const openPreview = async (fullscreen: boolean) => {
    setPreviewMenu(null);
    if (!video?.path) {
      setStatus('请先导入视频');
      return;
    }
    try {
      await window.desktopAPI.openVideoPreview({
        videoPath: video.path,
        fullscreen,
        currentTimeMs,
      });
      setStatus(fullscreen ? '已打开全屏视频预览窗口' : '已打开窗口化视频预览');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '打开视频预览失败');
    }
  };

  const playNextInFolder = () => {
    if (playbackMode !== 'folder' || !video?.path || folderVideos.length <= 1) return;
    const currentIndex = folderVideos.findIndex(item => item === video.path);
    const nextIndex = currentIndex >= 0 ? currentIndex + 1 : 0;
    if (nextIndex >= folderVideos.length) {
      setStatus('文件夹顺序播放已到最后一个视频');
      return;
    }
    void openVideoPath(folderVideos[nextIndex]).then(() => {
      window.setTimeout(() => videoRef.current?.toggle(), 350);
    });
  };

  return (
    <main className="app" onClick={() => setPreviewMenu(null)}>
      <header className="topbar">
        <div className="brand">
          <div className="logo">FS</div>
          <div>
            <strong>Funscript Studio 0.1.0-alpha.1 免费版</strong>
            <span>事件生成引擎 · 曲线编辑器 · 感知调试层</span>
          </div>
        </div>
        <div className="top-actions">
          <input ref={videoInputRef} hidden type="file" accept="video/*,.mkv,.webm,.mov,.avi,.m4v,.flv,.ts,.m2ts,.mts,.vob,.mpg,.mpeg,.wmv,.asf" onChange={event => {
            const file = event.target.files?.[0];
            if (file) importVideo(file);
            event.target.value = '';
          }} />
          <input ref={scriptInputRef} hidden type="file" multiple accept=".funscript,application/json" onChange={event => {
            const files = Array.from(event.target.files ?? []);
            if (files.length === 1) void importScript(files[0]);
            if (files.length > 1) void importScripts(files);
            event.target.value = '';
          }} />
          <input ref={perceptionInputRef} hidden type="file" accept=".json,application/json" onChange={event => {
            const file = event.target.files?.[0];
            if (file) void importPerception(file);
            event.target.value = '';
          }} />
          <button className="button secondary" onClick={openVideoPicker}>导入视频</button>
          <button className="button secondary" onClick={() => scriptInputRef.current?.click()}>导入脚本</button>
          <button className="button export" onClick={() => void exportAll()}>导出脚本</button>
          <select
            className="batch-mode-select"
            value={batchMode}
            disabled={analyzing || perceptionAnalyzing}
            title="批量生成模式"
            onChange={event => setBatchMode(event.target.value)}
          >
            <option value="hybrid">混合模式</option>
            <option value="hybrid_plus2">混合模式+2</option>
            <option value="energetic">高能模式</option>
            <option value="beat_matched">节拍优先模式</option>
          </select>
          <button className="button batch" disabled={analyzing || perceptionAnalyzing} onClick={() => void batchGenerate()}>批量生成脚本</button>
        </div>
      </header>

      <div className="workspace">
        <section className="main-column">
          <DevicePanel
            scripts={scripts}
            currentTimeMs={currentTimeMs}
            playing={playing}
          />

          <div
            ref={playerCardRef}
            className="player-card resizable-player"
            style={{
              width: previewSize.width ? `${previewSize.width}px` : '100%',
              maxWidth: '100%',
            }}
          >
            <div className="video-stage" style={{ height: `${previewSize.height}px` }}>
              <VideoPlayer
                ref={videoRef}
                src={video?.url}
                playing={playing}
                onPlayingChange={setPlaying}
                onTime={ms => setCurrentTimeMs(clampTime(ms, effectiveDurationMs))}
                onDuration={durationMs => setVideo(previous => previous ? { ...previous, durationMs: safeDuration(durationMs, 0) } : previous)}
                onVideoSize={fitPreviewToVideo}
                onImportVideo={openVideoPicker}
                onVideoFileDrop={importVideo}
                onVideoContextMenu={(x, y) => setPreviewMenu({ x, y })}
                onEndedPlayback={playNextInFolder}
              />
              <PerceptionOverlay perception={perception} currentTimeMs={currentTimeMs} enabled={overlayEnabled} />
              <button
                className="resize-handle resize-handle-right"
                type="button"
                title="左右拖动调整预览窗口宽度"
                onPointerDown={event => startPreviewResize('right', event)}
              />
              <button
                className="resize-handle resize-handle-bottom"
                type="button"
                title="上下拖动调整预览窗口高度"
                onPointerDown={event => startPreviewResize('bottom', event)}
              />
              <button
                className="resize-handle resize-handle-corner"
                type="button"
                title="拖动同时调整预览窗口宽度和高度"
                onPointerDown={event => startPreviewResize('corner', event)}
              />
            </div>
            <div className="transport">
              <button onClick={() => videoRef.current?.step(-1)}>◀|</button>
              <button className="play" onClick={() => videoRef.current?.toggle()}>{playing ? '暂停' : '播放'}</button>
              <button
                className={playbackMode === 'folder' ? 'playback-mode active' : 'playback-mode'}
                title="切换播放结束后的行为"
                onClick={() => setPlaybackMode(previous => previous === 'single' ? 'folder' : 'single')}
              >
                {playbackMode === 'single' ? '单个停止' : '文件夹顺播'}
              </button>
              <button onClick={() => videoRef.current?.step(1)}>|▶</button>
              <span className="transport-time">{formatTime(currentTimeMs)} / {formatTime(video?.durationMs ?? 0)}</span>
              <input
                type="range"
                min="0"
                max={effectiveDurationMs}
                value={clampTime(currentTimeMs, effectiveDurationMs)}
                onChange={event => seek(Number(event.target.value))}
              />
            </div>
          </div>

          <AxisPanel
            active={axis}
            counts={counts}
            locked={locked}
            onChange={setAxis}
            onToggleLock={target => setLocked(previous => ({ ...previous, [target]: !previous[target] }))}
          />

          <div className="quick-generate-panel">
            <button className="button quick" disabled={!video || !safeDuration(video.durationMs, 0) || analyzing} onClick={() => void generate()}>
              {analyzing ? '生成中…' : '快速生成（不推荐）'}
            </button>
            <span>基础音视频节奏生成，只生成主轴；推荐优先使用下方混合生成。</span>
          </div>

          <PerceptionTimeline
            perception={perception}
            currentTimeMs={currentTimeMs}
            onSeek={seek}
          />

          <PerceptionDebugPanel
            perception={perception}
            currentTimeMs={currentTimeMs}
            analyzing={perceptionAnalyzing}
            onAnalyze={() => void analyzePerception()}
            onImport={() => perceptionInputRef.current?.click()}
            onExport={() => void exportPerception()}
            onToggleOverlay={() => setOverlayEnabled(previous => !previous)}
            overlayEnabled={overlayEnabled}
          />

          <HybridGeneratePanel
            disabled={!video || analyzing}
            hasPerception={Boolean(perception)}
            onGenerate={generateHybrid}
            summary={hybridSummary}
          />

          <SimilarSegmentsPanel segments={similarSegments} />

          <TimelineEditor
            actions={currentScript.actions}
            durationMs={effectiveDurationMs}
            currentTimeMs={clampTime(currentTimeMs, effectiveDurationMs)}
            zoom={zoom}
            viewStartMs={timelineViewStart}
            curveMode={curveMode}
            onZoom={setZoom}
            onViewStart={setTimelineViewStart}
            onSeek={seek}
            onPreview={actions => applyActions(actions, false)}
            onCommit={actions => applyActions(actions, true)}
            onDeleteSelected={() => applyActions(currentScript.actions.filter(action => !action.selected), true)}
          />
        </section>

        <ScriptEditor
          actions={currentScript.actions}
          currentTimeMs={currentTimeMs}
          curveMode={curveMode}
          canUndo={currentHistory.past.length > 0}
          canRedo={currentHistory.future.length > 0}
          onUndo={undo}
          onRedo={redo}
          onCurveMode={applyMode}
          onSmooth={() => applyActions(smoothActions(currentScript.actions), true)}
          onIntensify={() => applyActions(intensifyActions(currentScript.actions), true)}
          onChange={actions => applyActions(actions, true)}
          onSeek={seek}
        />
      </div>

      {previewMenu ? (
        <div
          className="preview-context-menu"
          style={{ left: previewMenu.x, top: previewMenu.y }}
          onClick={event => event.stopPropagation()}
        >
          <button type="button" onClick={() => void openPreview(false)}>窗口化视频预览</button>
          <button type="button" onClick={() => void openPreview(true)}>全屏视频预览</button>
        </div>
      ) : null}

      <footer className="statusbar">
        <span className={(analyzing || perceptionAnalyzing) ? 'status-dot busy' : 'status-dot'} />
        <span>{status}</span>
        <div className="status-spacer" />
        <button disabled={!currentScript.actions.length} onClick={() => applyActions(currentScript.actions.map(action => ({ ...action, selected: false })), true)}>清除选择</button>
        <span>{video?.name ?? '未选择视频'}</span>
      </footer>
    </main>
  );
}
