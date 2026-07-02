import { useMemo, useRef, useState } from 'react';
import type { FunscriptAction } from '../core/types';

interface Props {
  actions: FunscriptAction[];
  durationMs: number;
  currentTimeMs: number;
  zoom: number;
  onZoom(zoom: number): void;
  onSeek(ms: number): void;
  onChange(actions: FunscriptAction[]): void;
}

type DragState = {
  index: number;
  startX: number;
  startY: number;
  originals: FunscriptAction[];
  bulk: boolean;
};

const WIDTH = 1200;
const HEIGHT = 330;
const TOP = 28;
const BOTTOM = 28;
const graphHeight = HEIGHT - TOP - BOTTOM;

export function TimelineEditor({
  actions,
  durationMs,
  currentTimeMs,
  zoom,
  onZoom,
  onSeek,
  onChange
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);
  const visibleDuration = Math.max(1000, durationMs / zoom);
  const maxStart = Math.max(0, durationMs - visibleDuration);
  const viewStart = Math.min(maxStart, Math.max(0, currentTimeMs - visibleDuration / 2));
  const viewEnd = viewStart + visibleDuration;

  const xAt = (at: number) => ((at - viewStart) / visibleDuration) * WIDTH;
  const yAt = (pos: number) => TOP + ((100 - pos) / 100) * graphHeight;
  const timeAt = (x: number) => viewStart + (x / WIDTH) * visibleDuration;
  const posAt = (y: number) => 100 - ((y - TOP) / graphHeight) * 100;

  const localPoint = (event: React.PointerEvent<SVGElement>) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * WIDTH,
      y: ((event.clientY - rect.top) / rect.height) * HEIGHT
    };
  };

  const visibleActions = useMemo(
    () => actions.map((action, index) => ({ action, index }))
      .filter(({ action }) => action.at >= viewStart - 100 && action.at <= viewEnd + 100),
    [actions, viewStart, viewEnd]
  );

  const curve = visibleActions.map(({ action }) => `${xAt(action.at)},${yAt(action.pos)}`).join(' ');

  const onPointerMove = (event: React.PointerEvent<SVGSVGElement>) => {
    if (!drag) return;
    const point = localPoint(event);
    const dxMs = ((point.x - drag.startX) / WIDTH) * visibleDuration;
    const dyPos = -((point.y - drag.startY) / graphHeight) * 100;
    const next = drag.originals.map((action, index) => {
      const selected = action.selected || index === drag.index;
      if (!selected || (!drag.bulk && index !== drag.index)) return action;
      return {
        ...action,
        at: drag.bulk ? Math.max(0, Math.min(durationMs, Math.round(action.at + dxMs))) : action.at,
        pos: Math.max(0, Math.min(100, Math.round(action.pos + dyPos)))
      };
    }).sort((a, b) => a.at - b.at);
    onChange(next);
  };

  const addOrSeek = (event: React.PointerEvent<SVGSVGElement>) => {
    if (event.target !== event.currentTarget) return;
    const point = localPoint(event);
    if (point.y >= TOP && point.y <= HEIGHT - BOTTOM) {
      const next = [...actions, {
        at: Math.round(timeAt(point.x)),
        pos: Math.round(Math.max(0, Math.min(100, posAt(point.y))))
      }].sort((a, b) => a.at - b.at);
      onChange(next);
    } else {
      onSeek(Math.max(0, Math.min(durationMs, timeAt(point.x))));
    }
  };

  const deleteSelected = () => {
    const selected = actions.filter(action => action.selected);
    if (selected.length) onChange(actions.filter(action => !action.selected));
  };

  return (
    <section className="timeline-card" onKeyDown={event => {
      if (event.key === 'Delete' || event.key === 'Backspace') deleteSelected();
    }} tabIndex={0}>
      <div className="timeline-toolbar">
        <div>
          <strong>Funscript 曲线</strong>
          <span>点击空白添加 · 拖动节点改位置 · Shift+拖动批量调整 · Delete 删除</span>
        </div>
        <div className="zoom-control">
          <button onClick={() => onZoom(Math.max(1, zoom / 1.5))}>−</button>
          <span>{zoom.toFixed(1)}×</span>
          <button onClick={() => onZoom(Math.min(16, zoom * 1.5))}>＋</button>
        </div>
      </div>
      <div className="timeline-scroll">
        <svg
          ref={svgRef}
          className="timeline-svg"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          onPointerDown={addOrSeek}
          onPointerMove={onPointerMove}
          onPointerUp={() => setDrag(null)}
          onPointerCancel={() => setDrag(null)}
        >
          <defs>
            <linearGradient id="curveFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#7c5cff" stopOpacity=".4" />
              <stop offset="1" stopColor="#7c5cff" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 25, 50, 75, 100].map(pos => (
            <g key={pos}>
              <line x1="0" x2={WIDTH} y1={yAt(pos)} y2={yAt(pos)} className="grid-line" />
              <text x="8" y={yAt(pos) - 5} className="grid-label">{pos}</text>
            </g>
          ))}
          {Array.from({ length: 9 }, (_, index) => {
            const time = viewStart + (index / 8) * visibleDuration;
            const x = (index / 8) * WIDTH;
            return (
              <g key={index}>
                <line x1={x} x2={x} y1={TOP} y2={HEIGHT - BOTTOM} className="time-line" />
                <text x={x + 5} y={HEIGHT - 8} className="time-label">{(time / 1000).toFixed(1)}s</text>
              </g>
            );
          })}
          {curve && (
            <>
              <polygon points={`${curve} ${xAt(visibleActions.at(-1)!.action.at)},${HEIGHT - BOTTOM} ${xAt(visibleActions[0].action.at)},${HEIGHT - BOTTOM}`} fill="url(#curveFill)" />
              <polyline points={curve} className="curve-line" />
            </>
          )}
          {visibleActions.map(({ action, index }) => (
            <circle
              key={`${action.at}-${index}`}
              cx={xAt(action.at)}
              cy={yAt(action.pos)}
              r={action.selected ? 8 : 6}
              className={action.selected ? 'keyframe selected' : 'keyframe'}
              onPointerDown={event => {
                event.stopPropagation();
                event.currentTarget.setPointerCapture(event.pointerId);
                const point = localPoint(event);
                const next = actions.map((item, itemIndex) => ({
                  ...item,
                  selected: event.shiftKey ? (item.selected || itemIndex === index) : itemIndex === index
                }));
                onChange(next);
                setDrag({ index, startX: point.x, startY: point.y, originals: next, bulk: event.shiftKey });
              }}
              onDoubleClick={() => onChange(actions.filter((_, itemIndex) => itemIndex !== index))}
            />
          ))}
          {currentTimeMs >= viewStart && currentTimeMs <= viewEnd && (
            <g className="playhead">
              <line x1={xAt(currentTimeMs)} x2={xAt(currentTimeMs)} y1="0" y2={HEIGHT} />
              <path d={`M ${xAt(currentTimeMs) - 7} 0 L ${xAt(currentTimeMs) + 7} 0 L ${xAt(currentTimeMs)} 12 Z`} />
            </g>
          )}
        </svg>
      </div>
    </section>
  );
}
