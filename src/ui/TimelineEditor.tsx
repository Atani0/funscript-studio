import { useEffect, useMemo, useRef, useState } from 'react';
import {
  boxSelectActions,
  moveSelectedActions,
  selectAction,
} from '../app/timeline_controller';
import type { CurveMode, FunscriptAction } from '../core/types';

interface Props {
  actions: FunscriptAction[];
  durationMs: number;
  currentTimeMs: number;
  zoom: number;
  viewStartMs: number;
  curveMode: CurveMode;
  onZoom(zoom: number): void;
  onViewStart(ms: number): void;
  onSeek(ms: number): void;
  onPreview(actions: FunscriptAction[]): void;
  onCommit(actions: FunscriptAction[]): void;
  onDeleteSelected(): void;
}

type DragState =
  | { kind: 'keys'; startX: number; startY: number; originals: FunscriptAction[]; moveTime: boolean }
  | { kind: 'box'; startX: number; startY: number; currentX: number; currentY: number; additive: boolean }
  | { kind: 'playhead' };

const WIDTH = 1800;
const HEIGHT = 380;
const TOP = 34;
const BOTTOM = 34;
const graphHeight = HEIGHT - TOP - BOTTOM;

export function TimelineEditor({
  actions,
  durationMs,
  currentTimeMs,
  zoom,
  viewStartMs,
  curveMode,
  onZoom,
  onViewStart,
  onSeek,
  onPreview,
  onCommit,
  onDeleteSelected,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [hoverMs, setHoverMs] = useState<number | null>(null);
  const safeDurationMs = Number.isFinite(durationMs) && durationMs > 0 ? durationMs : 10_000;
  const safeZoom = Number.isFinite(zoom) && zoom > 0 ? zoom : 1;
  const safeCurrentTimeMs = Number.isFinite(currentTimeMs) ? Math.max(0, Math.min(safeDurationMs, currentTimeMs)) : 0;
  const visibleDuration = Math.max(500, safeDurationMs / safeZoom);
  const maxStart = Math.max(0, safeDurationMs - visibleDuration);
  const viewStart = Math.min(maxStart, Math.max(0, Number.isFinite(viewStartMs) ? viewStartMs : 0));
  const viewEnd = viewStart + visibleDuration;

  useEffect(() => {
    if (viewStartMs > maxStart) onViewStart(maxStart);
    if (viewStartMs < 0) onViewStart(0);
  }, [maxStart, onViewStart, viewStartMs]);

  const xAt = (at: number) => ((at - viewStart) / visibleDuration) * WIDTH;
  const yAt = (pos: number) => TOP + ((100 - pos) / 100) * graphHeight;
  const timeAt = (x: number) => viewStart + (x / WIDTH) * visibleDuration;
  const posAt = (y: number) => 100 - ((y - TOP) / graphHeight) * 100;
  const clampTime = (ms: number) => Math.max(0, Math.min(safeDurationMs, Number.isFinite(ms) ? ms : 0));
  const clampPos = (pos: number) => Math.max(0, Math.min(100, pos));

  const localPoint = (event: React.PointerEvent<SVGElement> | React.WheelEvent<SVGSVGElement>) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * WIDTH,
      y: ((event.clientY - rect.top) / rect.height) * HEIGHT,
    };
  };

  const visibleActions = useMemo(
    () => actions.map((action, index) => ({ action, index }))
      .filter(({ action }) => action.at >= viewStart - 200 && action.at <= viewEnd + 200),
    [actions, viewStart, viewEnd],
  );

  const curvePath = useMemo(() => buildCurvePath(visibleActions.map(({ action }) => action), xAt, yAt, curveMode), [visibleActions, curveMode]);
  const selectedCount = actions.filter(action => action.selected).length;

  const onPointerMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const point = localPoint(event);
    setHoverMs(clampTime(timeAt(point.x)));
    if (!drag) return;
    if (drag.kind === 'playhead') {
      onSeek(clampTime(timeAt(point.x)));
      return;
    }
    if (drag.kind === 'keys') {
      const deltaMs = ((point.x - drag.startX) / WIDTH) * visibleDuration;
      const deltaPos = -((point.y - drag.startY) / graphHeight) * 100;
      onPreview(moveSelectedActions(drag.originals, deltaMs, deltaPos, safeDurationMs, drag.moveTime));
      return;
    }
    setDrag({ ...drag, currentX: point.x, currentY: point.y });
    onPreview(boxSelectActions(actions, timeAt(drag.startX), timeAt(point.x), posAt(drag.startY), posAt(point.y), drag.additive));
  };

  const finishDrag = () => {
    if (drag?.kind === 'box') {
      const moved = Math.hypot(drag.currentX - drag.startX, drag.currentY - drag.startY);
      if (moved < 4) {
        onSeek(clampTime(timeAt(drag.startX)));
      } else {
        onCommit(actions);
      }
      setDrag(null);
      return;
    }
    if (drag && drag.kind !== 'playhead') onCommit(actions);
    setDrag(null);
  };

  const addOrSelect = (event: React.PointerEvent<SVGSVGElement>) => {
    const point = localPoint(event);
    if (event.altKey || event.button === 2) {
      onSeek(clampTime(timeAt(point.x)));
      return;
    }
    if (point.y >= TOP && point.y <= HEIGHT - BOTTOM && event.detail >= 2) {
      onCommit([...actions, {
        at: Math.round(clampTime(timeAt(point.x))),
        pos: Math.round(clampPos(posAt(point.y))),
        easing: curveMode,
      }].sort((a, b) => a.at - b.at));
      return;
    }
    setDrag({ kind: 'box', startX: point.x, startY: point.y, currentX: point.x, currentY: point.y, additive: event.shiftKey });
  };

  return (
    <section
      className="timeline-card"
      tabIndex={0}
      onKeyDown={event => {
        const key = event.key.toLowerCase();
        if (key === 'delete' || key === 'backspace') onDeleteSelected();
        if (key === 'a' && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          onCommit(actions.map(action => ({ ...action, selected: true })));
        }
      }}
    >
      <div className="timeline-toolbar">
        <div>
          <strong>专业曲线时间轴</strong>
          <span>双击添加节点 · 拖动节点改位置 · 框选多选 · Shift 多选 · 拖动红线同步视频 · Ctrl+滚轮缩放</span>
        </div>
        <div className="zoom-control">
          <button onClick={() => onZoom(Math.max(1, zoom / 1.35))}>－</button>
          <span>{zoom.toFixed(1)}×</span>
          <button onClick={() => onZoom(Math.min(64, zoom * 1.35))}>＋</button>
        </div>
      </div>
      <div className="timeline-scroll">
        <svg
          ref={svgRef}
          className="timeline-svg"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          onPointerDown={addOrSelect}
          onPointerMove={onPointerMove}
          onPointerLeave={() => setHoverMs(null)}
          onPointerUp={finishDrag}
          onPointerCancel={() => setDrag(null)}
          onWheel={event => {
            if (!event.ctrlKey && !event.metaKey) return;
            event.preventDefault();
            const factor = event.deltaY < 0 ? 1.16 : 1 / 1.16;
            onZoom(Math.max(1, Math.min(64, zoom * factor)));
          }}
        >
          <defs>
            <linearGradient id="curveFillProfessional" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#70f1df" stopOpacity=".26" />
              <stop offset="1" stopColor="#7c5cff" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 25, 50, 75, 100].map(pos => (
            <g key={pos}>
              <line x1="0" x2={WIDTH} y1={yAt(pos)} y2={yAt(pos)} className="grid-line" />
              <text x="8" y={yAt(pos) - 5} className="grid-label">{pos}</text>
            </g>
          ))}
          {Array.from({ length: 13 }, (_, index) => {
            const time = viewStart + (index / 12) * visibleDuration;
            const x = (index / 12) * WIDTH;
            return (
              <g key={index}>
                <line x1={x} x2={x} y1={TOP} y2={HEIGHT - BOTTOM} className="time-line" />
                <text x={x + 5} y={HEIGHT - 9} className="time-label">{(time / 1000).toFixed(2)}秒</text>
              </g>
            );
          })}

          {curvePath && (
            <>
              <path d={`${curvePath} L ${xAt(visibleActions.at(-1)!.action.at)} ${HEIGHT - BOTTOM} L ${xAt(visibleActions[0].action.at)} ${HEIGHT - BOTTOM} Z`} fill="url(#curveFillProfessional)" />
              <path d={curvePath} className={`curve-line ${curveMode}`} />
            </>
          )}

          {visibleActions.map(({ action, index }) => (
            <circle
              key={`${action.at}-${index}`}
              cx={xAt(action.at)}
              cy={yAt(action.pos)}
              r={action.selected ? 8 : 5.5}
              className={action.selected ? 'keyframe selected' : 'keyframe'}
              onPointerDown={event => {
                event.stopPropagation();
                event.currentTarget.setPointerCapture(event.pointerId);
                const selected = selectAction(actions, index, event.shiftKey || event.metaKey || event.ctrlKey);
                const withCurrentSelected = selected[index]?.selected ? selected : selectAction(selected, index, true);
                onPreview(withCurrentSelected);
                const point = localPoint(event);
                setDrag({ kind: 'keys', startX: point.x, startY: point.y, originals: withCurrentSelected, moveTime: event.shiftKey });
              }}
              onDoubleClick={() => onCommit(actions.filter((_, itemIndex) => itemIndex !== index))}
            />
          ))}

          {drag?.kind === 'box' && (
            <rect
              className="selection-box"
              x={Math.min(drag.startX, drag.currentX)}
              y={Math.min(drag.startY, drag.currentY)}
              width={Math.abs(drag.currentX - drag.startX)}
              height={Math.abs(drag.currentY - drag.startY)}
            />
          )}

          {hoverMs !== null && (
            <line x1={xAt(hoverMs)} x2={xAt(hoverMs)} y1={TOP} y2={HEIGHT - BOTTOM} className="hover-line" />
          )}

          {safeCurrentTimeMs >= viewStart && safeCurrentTimeMs <= viewEnd && (
            <g className="playhead">
              <rect
                x={xAt(safeCurrentTimeMs) - 10}
                y="0"
                width="20"
                height={HEIGHT}
                className="playhead-hit"
                onPointerDown={event => {
                  event.stopPropagation();
                  event.currentTarget.setPointerCapture(event.pointerId);
                  setDrag({ kind: 'playhead' });
                  const point = localPoint(event);
                  onSeek(clampTime(timeAt(point.x)));
                }}
              />
              <line x1={xAt(safeCurrentTimeMs)} x2={xAt(safeCurrentTimeMs)} y1="0" y2={HEIGHT} />
              <path d={`M ${xAt(safeCurrentTimeMs) - 8} 0 L ${xAt(safeCurrentTimeMs) + 8} 0 L ${xAt(safeCurrentTimeMs)} 14 Z`} />
            </g>
          )}
        </svg>
      </div>
      <div className="timeline-panbar">
        <input
          type="range"
          min="0"
          max={Math.max(0, Math.round(maxStart))}
          step={Math.max(1, Math.round(visibleDuration / 400))}
          value={Math.round(viewStart)}
          disabled={maxStart <= 0}
          onChange={event => onViewStart(Number(event.target.value))}
        />
      </div>
      <div className="timeline-footer">
        <span>显示范围：{(viewStart / 1000).toFixed(2)}秒 – {(viewEnd / 1000).toFixed(2)}秒</span>
        <span>已选 {selectedCount} 个节点</span>
        <span>{Math.round(visibleDuration / WIDTH)} 毫秒/像素</span>
      </div>
    </section>
  );
}

function buildCurvePath(
  actions: FunscriptAction[],
  xAt: (time: number) => number,
  yAt: (pos: number) => number,
  fallbackMode: CurveMode,
) {
  if (!actions.length) return '';
  if (actions.length === 1) return `M ${xAt(actions[0].at)} ${yAt(actions[0].pos)}`;
  let path = `M ${xAt(actions[0].at)} ${yAt(actions[0].pos)}`;
  for (let index = 1; index < actions.length; index += 1) {
    const previous = actions[index - 1];
    const current = actions[index];
    const mode = previous.easing ?? fallbackMode;
    const x1 = xAt(previous.at);
    const y1 = yAt(previous.pos);
    const x2 = xAt(current.at);
    const y2 = yAt(current.pos);
    if (mode === 'linear') {
      path += ` L ${x2} ${y2}`;
    } else {
      const curve = mode === 'bezier' ? 0.45 : 0.32;
      const c1x = x1 + (x2 - x1) * curve;
      const c2x = x2 - (x2 - x1) * curve;
      path += ` C ${c1x} ${y1}, ${c2x} ${y2}, ${x2} ${y2}`;
    }
  }
  return path;
}
