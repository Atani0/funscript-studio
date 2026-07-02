interface Props {
  segments?: unknown[];
}

export function SimilarSegmentsPanel({ segments = [] }: Props) {
  return (
    <section className="learning-card">
      <div className="perception-heading">
        <strong>相似片段</strong>
        <span>{segments.length} 个匹配</span>
      </div>
      <pre>{JSON.stringify(segments.slice(0, 5), null, 2)}</pre>
    </section>
  );
}
