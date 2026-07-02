import { useEffect, useRef, useState } from 'react';
import { axes } from '../core/axis_manager';
import type { AxisName, AxisScripts, FunscriptAction } from '../core/types';

type DeviceType = 'OSR2' | 'SR6';
type AxisLimit = { min: number; max: number };
type AxisLimits = Record<AxisName, AxisLimit>;
type AxisPositions = Record<AxisName, number>;
const LIMIT_STORAGE_KEY = 'funscript-studio.device-axis-limits.v1';

type SerialPortLike = {
  open(options: { baudRate: number }): Promise<void>;
  close(): Promise<void>;
  writable?: WritableStream<Uint8Array> | null;
};

type SerialNavigator = Navigator & {
  serial?: {
    requestPort(options?: { filters?: unknown[] }): Promise<SerialPortLike>;
  };
};

interface Props {
  scripts: AxisScripts;
  currentTimeMs: number;
  playing: boolean;
}

const axisToTCode: Record<AxisName, string> = {
  stroke: 'L0',
  surge: 'L1',
  sway: 'L2',
  twist: 'R0',
  roll: 'R1',
  pitch: 'R2',
};

const axisLabels: Record<AxisName, string> = {
  stroke: '升降',
  surge: '前后',
  sway: '左右',
  twist: '旋转',
  roll: '侧倾',
  pitch: '俯仰',
};

const createDefaultLimits = (): AxisLimits => ({
  stroke: { min: 20, max: 80 },
  surge: { min: 20, max: 80 },
  sway: { min: 20, max: 80 },
  twist: { min: 20, max: 80 },
  roll: { min: 20, max: 80 },
  pitch: { min: 20, max: 80 },
});

const loadStoredLimits = (): AxisLimits => {
  const defaults = createDefaultLimits();
  try {
    const raw = window.localStorage.getItem(LIMIT_STORAGE_KEY);
    if (!raw) return defaults;
    const parsed = JSON.parse(raw) as Partial<Record<AxisName, Partial<AxisLimit>>>;
    const restored = { ...defaults };
    for (const axis of axes) {
      const item = parsed[axis];
      if (!item) continue;
      restored[axis] = normalizeLimit({
        min: Number(item.min),
        max: Number(item.max),
      });
    }
    return restored;
  } catch {
    return defaults;
  }
};

const createCenteredPositions = (): AxisPositions => ({
  stroke: 50,
  surge: 50,
  sway: 50,
  twist: 50,
  roll: 50,
  pitch: 50,
});

const clamp = (value: number, min = 0, max = 100) =>
  Math.max(min, Math.min(max, Number.isFinite(value) ? value : 50));

const interpolatePos = (actions: FunscriptAction[], timeMs: number) => {
  if (!actions.length) return 50;
  if (timeMs <= actions[0].at) return actions[0].pos;
  for (let index = 1; index < actions.length; index += 1) {
    const previous = actions[index - 1];
    const current = actions[index];
    if (timeMs <= current.at) {
      const span = Math.max(1, current.at - previous.at);
      const ratio = clamp((timeMs - previous.at) / span, 0, 1);
      return previous.pos + (current.pos - previous.pos) * ratio;
    }
  }
  return actions.at(-1)?.pos ?? 50;
};

const normalizeLimit = (limit: AxisLimit): AxisLimit => {
  const min = clamp(Math.min(limit.min, limit.max - 1), 0, 99);
  const max = clamp(Math.max(limit.max, min + 1), 1, 100);
  return { min, max };
};

const applyAxisLimit = (axis: AxisName, pos: number, limits: AxisLimits) => {
  const limit = normalizeLimit(limits[axis]);
  return limit.min + (clamp(pos) / 100) * (limit.max - limit.min);
};

const tcodeValue = (pos: number) =>
  String(Math.round(clamp(pos) * 99.99)).padStart(4, '0');

const buildTCode = (
  positions: Partial<Record<AxisName, number>>,
  limits: AxisLimits,
  intervalMs?: number,
) => {
  const suffix = intervalMs ? `I${Math.max(1, Math.round(intervalMs))}` : '';
  const command = axes
    .filter(axis => typeof positions[axis] === 'number')
    .map(axis => `${axisToTCode[axis]}${tcodeValue(applyAxisLimit(axis, positions[axis] ?? 50, limits))}${suffix}`)
    .join('');
  return command ? `${command}\n` : '';
};

const applyPositionsToLimits = (
  positions: Partial<Record<AxisName, number>>,
  limits: AxisLimits,
  previous: AxisPositions,
) => {
  const next = { ...previous };
  for (const axis of axes) {
    if (typeof positions[axis] === 'number') {
      next[axis] = Math.round(applyAxisLimit(axis, positions[axis] ?? 50, limits));
    }
  }
  return next;
};

export function DevicePanel({ scripts, currentTimeMs, playing }: Props) {
  const [deviceType, setDeviceType] = useState<DeviceType>('OSR2');
  const [connected, setConnected] = useState(false);
  const [syncEnabled, setSyncEnabled] = useState(true);
  const [status, setStatus] = useState('未连接');
  const [limits, setLimits] = useState<AxisLimits>(() => loadStoredLimits());
  const [currentPositions, setCurrentPositions] = useState<AxisPositions>(() => createCenteredPositions());
  const portRef = useRef<SerialPortLike | null>(null);
  const writerRef = useRef<WritableStreamDefaultWriter<Uint8Array> | null>(null);
  const encoderRef = useRef(new TextEncoder());
  const scriptsRef = useRef(scripts);
  const timeRef = useRef(currentTimeMs);
  const limitsRef = useRef(limits);
  const positionsRef = useRef(currentPositions);
  const sendingRef = useRef(false);
  const lastCommandRef = useRef('');

  useEffect(() => {
    scriptsRef.current = scripts;
  }, [scripts]);

  useEffect(() => {
    timeRef.current = currentTimeMs;
  }, [currentTimeMs]);

  useEffect(() => {
    limitsRef.current = limits;
    window.localStorage.setItem(LIMIT_STORAGE_KEY, JSON.stringify(limits));
    setCurrentPositions(previous => {
      const next = { ...previous };
      for (const axis of axes) {
        const limit = normalizeLimit(limits[axis]);
        next[axis] = Math.round(clamp(previous[axis], limit.min, limit.max));
      }
      return next;
    });
  }, [limits]);

  useEffect(() => {
    positionsRef.current = currentPositions;
  }, [currentPositions]);

  const sendRaw = async (command: string) => {
    if (!command || !writerRef.current) return;
    await writerRef.current.write(encoderRef.current.encode(command));
  };

  const sendPositions = async (positions: Partial<Record<AxisName, number>>, intervalMs?: number) => {
    const activeLimits = limitsRef.current;
    const command = buildTCode(positions, activeLimits, intervalMs);
    if (!command) return;
    await sendRaw(command);
    lastCommandRef.current = command.trim();
    setCurrentPositions(previous => applyPositionsToLimits(positions, activeLimits, previous));
  };

  const connect = async () => {
    const serial = (navigator as SerialNavigator).serial;
    if (!serial) {
      setStatus('当前环境不支持 USB 串口连接，请使用新版 Chromium/Electron 运行。');
      return;
    }
    try {
      setStatus('正在请求 USB 串口设备，请选择 OSR2/SR6 对应的 COM 设备…');
      const port = await serial.requestPort({ filters: [] });
      await port.open({ baudRate: 115200 });
      const writer = port.writable?.getWriter();
      if (!writer) throw new Error('无法打开 USB 串口写入通道');
      portRef.current = port;
      writerRef.current = writer;
      setConnected(true);
      setStatus(`${deviceType} 已连接 · USB 串口 · 115200`);
      await sendPositions(createCenteredPositions());
    } catch (error) {
      setConnected(false);
      setStatus(error instanceof Error ? error.message : 'USB 设备连接失败');
    }
  };

  const disconnect = async () => {
    try {
      await sendPositions(createCenteredPositions());
      writerRef.current?.releaseLock();
      writerRef.current = null;
      await portRef.current?.close();
    } catch {
      // 串口可能已经被系统释放，关闭阶段忽略即可。
    } finally {
      portRef.current = null;
      setConnected(false);
      setStatus('已断开');
    }
  };

  const testAll = async (pos: number) => {
    await sendPositions({ stroke: pos, surge: pos, sway: pos, twist: pos, roll: pos, pitch: pos });
    setStatus(`已发送测试位置：${pos}`);
  };

  const sendPlaybackFrame = async () => {
    if (sendingRef.current) return;
    sendingRef.current = true;
    try {
      const positions: Partial<Record<AxisName, number>> = {};
      for (const axis of axes) {
        const actions = scriptsRef.current[axis].actions;
        if (actions.length) positions[axis] = interpolatePos(actions, timeRef.current);
      }
      await sendPositions(positions, 16);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '设备同步失败');
    } finally {
      sendingRef.current = false;
    }
  };

  const updateLimit = (axis: AxisName, edge: keyof AxisLimit, value: number) => {
    setLimits(previous => {
      const current = previous[axis];
      const next: AxisLimit = edge === 'min'
        ? { min: Math.min(clamp(value), current.max - 1), max: current.max }
        : { min: current.min, max: Math.max(clamp(value), current.min + 1) };
      return { ...previous, [axis]: normalizeLimit(next) };
    });
  };

  useEffect(() => {
    const positions: Partial<Record<AxisName, number>> = {};
    for (const axis of axes) {
      const actions = scripts[axis].actions;
      if (actions.length) positions[axis] = interpolatePos(actions, currentTimeMs);
    }
    if (Object.keys(positions).length) {
      setCurrentPositions(previous => applyPositionsToLimits(positions, limitsRef.current, previous));
    }
  }, [scripts, currentTimeMs]);

  useEffect(() => {
    if (!connected || !syncEnabled || !playing) return;
    void sendPlaybackFrame();
    const timer = window.setInterval(() => {
      void sendPlaybackFrame();
    }, 16);
    return () => window.clearInterval(timer);
  }, [connected, syncEnabled, playing]);

  useEffect(() => () => {
    void disconnect();
  }, []);

  useEffect(() => {
    const releaseDevice = () => {
      void disconnect();
    };
    window.addEventListener('beforeunload', releaseDevice);
    window.addEventListener('pagehide', releaseDevice);
    return () => {
      window.removeEventListener('beforeunload', releaseDevice);
      window.removeEventListener('pagehide', releaseDevice);
    };
  }, []);

  const activeAxes = axes.filter(axis => scripts[axis].actions.length > 0);

  return (
    <section className="device-panel">
      <div className="device-heading">
        <strong>设备连接 / 调试</strong>
        <span>{status}</span>
      </div>
      <select value={deviceType} onChange={event => setDeviceType(event.target.value as DeviceType)}>
        <option value="OSR2">OSR2</option>
        <option value="SR6">SR6</option>
      </select>
      <button type="button" disabled={connected} onClick={() => void connect()}>连接 USB 设备</button>
      <button type="button" disabled={!connected} onClick={() => void disconnect()}>断开</button>
      <label className="device-sync-toggle">
        <input
          type="checkbox"
          checked={syncEnabled}
          onChange={event => setSyncEnabled(event.target.checked)}
        />
        播放时同步
      </label>
      <button type="button" disabled={!connected} onClick={() => void testAll(50)}>居中</button>
      <button type="button" disabled={!connected} onClick={() => void testAll(15)}>低位</button>
      <button type="button" disabled={!connected} onClick={() => void testAll(85)}>高位</button>
      <span className="device-axis-hint">
        当前输出轴：{activeAxes.length ? activeAxes.map(axis => axisLabels[axis]).join(' / ') : '暂无脚本节点'}
        {connected && lastCommandRef.current ? ` · 最近命令：${lastCommandRef.current}` : ''}
      </span>

      <div className="device-limit-panel" aria-label="设备轴限位">
        <div className="device-limit-title">
          <strong>轴限位 / 实时位置</strong>
          <button type="button" className="device-limit-reset" onClick={() => setLimits(createDefaultLimits())}>重置限位</button>
        </div>
        {axes.map(axis => {
          const limit = normalizeLimit(limits[axis]);
          const position = clamp(currentPositions[axis]);
          return (
            <div className="device-limit-row" key={axis}>
              <span className="limit-axis">{axisLabels[axis]}</span>
              <input
                className="limit-value limit-value-input"
                aria-label={`${axisLabels[axis]}最低限位数值`}
                type="number"
                min={0}
                max={99}
                value={Math.round(limit.min)}
                onChange={event => updateLimit(axis, 'min', Number(event.target.value))}
              />
              <div className="dual-range" title={`${axisLabels[axis]}：限位 ${Math.round(limit.min)}-${Math.round(limit.max)}，实时 ${Math.round(position)}`}>
                <div
                  className="limit-active-range"
                  style={{ left: `${limit.min}%`, width: `${Math.max(1, limit.max - limit.min)}%` }}
                />
                <div className="limit-position-fill" style={{ width: `${position}%` }} />
                <input
                  aria-label={`${axisLabels[axis]}最低限位`}
                  type="range"
                  min={0}
                  max={100}
                  value={limit.min}
                  onChange={event => updateLimit(axis, 'min', Number(event.target.value))}
                />
                <input
                  aria-label={`${axisLabels[axis]}最高限位`}
                  type="range"
                  min={0}
                  max={100}
                  value={limit.max}
                  onChange={event => updateLimit(axis, 'max', Number(event.target.value))}
                />
              </div>
              <input
                className="limit-value limit-value-input"
                aria-label={`${axisLabels[axis]}最高限位数值`}
                type="number"
                min={1}
                max={100}
                value={Math.round(limit.max)}
                onChange={event => updateLimit(axis, 'max', Number(event.target.value))}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}
