import { formatTime } from '../app/video_controller';
import type { CurveMode, FunscriptAction } from '../core/types';

interface Props {
  actions: FunscriptAction[];
  currentTimeMs: number;
  curveMode: CurveMode;
  canUndo: boolean;
  canRedo: boolean;
  onUndo(): void;
  onRedo(): void;
  onCurveMode(mode: CurveMode): void;
  onSmooth(): void;
  onIntensify(): void;
  onChange(actions: FunscriptAction[]): void;
  onSeek(ms: number): void;
}

const curveModeLabel: Record<CurveMode, string> = {
  linear: '线性',
  smooth: '平滑',
  bezier: '贝塞尔',
};

const curveModeHelp: Record<CurveMode, string> = {
  linear: '线性：节点之间用直线连接，动作变化直接、清晰，适合需要精确卡点的片段。',
  smooth: '平滑：对节点做柔和过渡，减少突兀抖动，适合大多数自动生成后的初步修整。',
  bezier: '贝塞尔：使用更柔顺的曲线插值，适合手工精修节奏和速度变化；不会改变 funscript 标准格式。',
};

export function ScriptEditor({
  actions,
  currentTimeMs,
  curveMode,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onCurveMode,
  onSmooth,
  onIntensify,
  onChange,
  onSeek,
}: Props) {
  const nearest = actions.reduce((best, action) =>
    Math.abs(action.at - currentTimeMs) < Math.abs(best.at - currentTimeMs) ? action : best,
    actions[0] ?? { at: 0, pos: 50 });
  const selectedCount = actions.filter(action => action.selected).length;

  return (
    <aside className="inspector">
      <div className="inspector-heading">
        <strong>脚本编辑器</strong>
        <span>{actions.length} 个动作</span>
      </div>

      <div className="tool-grid">
        <button disabled={!canUndo} onClick={onUndo}>撤销</button>
        <button disabled={!canRedo} onClick={onRedo}>重做</button>
        <button disabled={!actions.length} onClick={onSmooth}>平滑当前轴</button>
        <button disabled={!actions.length} onClick={onIntensify}>加剧当前轴</button>
      </div>

      <div className="curve-tools">
        <small>曲线模式</small>
        {(['linear', 'smooth', 'bezier'] as CurveMode[]).map(mode => (
          <button
            key={mode}
            className={curveMode === mode ? 'active' : ''}
            onClick={() => onCurveMode(mode)}
            title={curveModeHelp[mode]}
          >
            {curveModeLabel[mode]}
          </button>
        ))}
      </div>

      <div className="nearest-card">
        <small>播放头附近节点</small>
        <b>{nearest.pos}</b>
        <span>{formatTime(nearest.at)}</span>
        <em>已选 {selectedCount} 个</em>
      </div>

      <div className="action-list">
        {actions.slice(0, 450).map((action, index) => (
          <button key={`${action.at}-${index}`} onClick={() => onSeek(action.at)} className={action.selected ? 'selected' : ''}>
            <input
              aria-label="时间毫秒"
              type="number"
              value={action.at}
              onClick={event => event.stopPropagation()}
              onChange={event => {
                const next = [...actions];
                next[index] = { ...action, at: Math.max(0, Number(event.target.value)) };
                onChange(next.sort((a, b) => a.at - b.at));
              }}
            />
            <input
              aria-label="位置"
              type="number"
              min="0"
              max="100"
              value={action.pos}
              onClick={event => event.stopPropagation()}
              onChange={event => {
                const next = [...actions];
                next[index] = { ...action, pos: Math.max(0, Math.min(100, Number(event.target.value))) };
                onChange(next);
              }}
            />
          </button>
        ))}
      </div>
    </aside>
  );
}
