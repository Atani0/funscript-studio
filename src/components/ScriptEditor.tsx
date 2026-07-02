import type { FunscriptAction } from '../core/types';

interface Props {
  actions: FunscriptAction[];
  currentTimeMs: number;
  onChange(actions: FunscriptAction[]): void;
  onSeek(ms: number): void;
}

export function ScriptEditor({ actions, currentTimeMs, onChange, onSeek }: Props) {
  const nearest = actions.reduce((best, action) =>
    Math.abs(action.at - currentTimeMs) < Math.abs(best.at - currentTimeMs) ? action : best,
    actions[0] ?? { at: 0, pos: 50 });

  return (
    <aside className="inspector">
      <div className="inspector-heading">
        <strong>节点检查器</strong>
        <span>{actions.length} actions</span>
      </div>
      <div className="nearest-card">
        <small>播放头附近</small>
        <b>{nearest.pos}</b>
        <span>@ {(nearest.at / 1000).toFixed(3)}s</span>
      </div>
      <div className="action-list">
        {actions.slice(0, 250).map((action, index) => (
          <button key={`${action.at}-${index}`} onClick={() => onSeek(action.at)} className={action.selected ? 'selected' : ''}>
            <input
              aria-label="时间"
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
