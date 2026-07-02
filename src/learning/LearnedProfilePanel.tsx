interface Props {
  profile?: Record<string, unknown> | null;
}

export function LearnedProfilePanel({ profile }: Props) {
  return (
    <section className="learning-card">
      <div className="perception-heading">
        <strong>学习参数</strong>
        <span>权重 / 幅度 / 密度 / 平滑度</span>
      </div>
      <pre>{JSON.stringify(profile ?? { message: '暂无已加载学习参数，混合生成会使用默认参数。' }, null, 2)}</pre>
    </section>
  );
}
