interface Props {
  disabled: boolean;
  hasPerception: boolean;
  onGenerate(options: { mode: string; style: string; useLearned: boolean; useSimilar: boolean }): Promise<void>;
  summary?: Record<string, unknown> | null;
}

export function HybridGeneratePanel({ disabled, hasPerception, onGenerate, summary }: Props) {
  const run = (mode: string, style = 'balanced') => {
    void onGenerate({ mode, style, useLearned: mode === 'learned_hybrid', useSimilar: mode === 'learned_hybrid' });
  };

  return (
    <section className="learning-card">
      <div className="perception-heading">
        <strong>混合生成器</strong>
        <span>音频定时 · 感知控幅 · 学习风格</span>
      </div>
      <div className="hybrid-buttons">
        <button disabled={disabled} onClick={() => run('hybrid', 'balanced')}>混合生成</button>
        <button disabled={disabled} onClick={() => run('hybrid_plus2', 'balanced')}>混合生成+2</button>
        <button disabled={disabled} onClick={() => run('hybrid', 'beat_matched')}>节拍优先</button>
        <button disabled={disabled} onClick={() => run('hybrid', 'energetic')}>高能模式</button>
        <button disabled={disabled || !hasPerception} onClick={() => run('learned_hybrid', 'balanced')}>学习混合生成</button>
      </div>
      <small>推荐：先在“感知层调试”里分析感知层，再使用混合生成。混合生成+2 会在默认混合结果上扩大两次振幅；高能模式现在只扩大一次振幅。</small>
      {summary ? <pre>{JSON.stringify(summary, null, 2)}</pre> : null}
    </section>
  );
}
