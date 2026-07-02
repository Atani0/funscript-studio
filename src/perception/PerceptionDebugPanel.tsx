import { useMemo, useState } from 'react';
import type { PerceptionTimeline } from '../core/perceptionTypes';

interface Props {
  perception?: PerceptionTimeline | null;
  currentTimeMs: number;
  analyzing: boolean;
  onAnalyze(): void;
  onImport(): void;
  onExport(): void;
  onToggleOverlay(): void;
  overlayEnabled: boolean;
}

type DebugTab = 'fusion' | 'audio' | 'visual' | 'interaction' | 'raw';

export function PerceptionDebugPanel({
  perception,
  currentTimeMs,
  analyzing,
  onAnalyze,
  onImport,
  onExport,
  onToggleOverlay,
  overlayEnabled,
}: Props) {
  const [tab, setTab] = useState<DebugTab>('fusion');
  const segment = useMemo(() => {
    if (!perception?.segments?.length) return null;
    return perception.segments.find(item => currentTimeMs >= item.start && currentTimeMs <= item.end) ?? perception.segments[0];
  }, [perception, currentTimeMs]);

  const content = tab === 'raw' ? perception : tab === 'fusion' ? segment : segment?.[tab];

  return (
    <section className="perception-debug">
      <div className="perception-heading">
        <strong>感知层调试</strong>
        <span>{perception ? `段数 ${perception.segments.length}` : '未分析'}</span>
      </div>
      <div className="perception-actions">
        <button disabled={analyzing} onClick={onAnalyze}>{analyzing ? '分析中…' : '分析感知层'}</button>
        <button onClick={onImport}>导入感知数据</button>
        <button disabled={!perception} onClick={onExport}>导出感知数据</button>
        <button onClick={onToggleOverlay}>{overlayEnabled ? '关闭叠加' : '打开叠加'}</button>
      </div>
      <div className="perception-tabs">
        {(['fusion', 'audio', 'visual', 'interaction', 'raw'] as const).map(item => (
          <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{tabLabel(item)}</button>
        ))}
      </div>
      <pre>{JSON.stringify(content ?? { message: '暂无当前时间点感知数据' }, null, 2)}</pre>
    </section>
  );
}

function tabLabel(tab: DebugTab) {
  return ({ fusion: '融合', audio: '音频', visual: '视觉', interaction: '互动', raw: '完整数据' })[tab];
}
