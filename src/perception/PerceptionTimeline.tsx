import type { PerceptionTimeline } from '../core/perceptionTypes';

interface Props {
  perception?: PerceptionTimeline | null;
  currentTimeMs: number;
  onSeek(ms: number): void;
}

export function PerceptionTimeline({ perception, currentTimeMs, onSeek }: Props) {
  if (!perception?.segments?.length) {
    return (
      <section className="perception-card">
        <strong>感知时间线</strong>
        <span>暂无感知数据，请先点击“分析感知层”。</span>
      </section>
    );
  }

  const duration = Math.max(1, perception.duration);
  return (
    <section className="perception-card">
      <div className="perception-heading">
        <strong>感知时间线</strong>
        <span>风格 {perception.summary.style} · 平均运动 {perception.summary.avgMotion.toFixed(2)} · 音频 {perception.summary.audioMode}</span>
      </div>
      <div className="perception-bars">
        <Track label="视觉" color="#70f1df" segments={perception.segments.map(s => [s.start, s.visual.motion_intensity])} duration={duration} onSeek={onSeek} />
        <Track label="姿态" color="#8a71ff" segments={perception.segments.map(s => [s.start, s.visual.body_motion_overall])} duration={duration} onSeek={onSeek} />
        <Track label="互动" color="#ffcf6b" segments={perception.segments.map(s => [s.start, s.interaction.interaction_intensity])} duration={duration} onSeek={onSeek} />
        <Track label="音频" color="#ff557d" segments={perception.segments.map(s => [s.start, Math.max(s.audio.beat_strength, s.audio.transient_strength)])} duration={duration} onSeek={onSeek} />
      </div>
      <div className="perception-playhead" style={{ left: `${Math.min(100, currentTimeMs / duration * 100)}%` }} />
    </section>
  );
}

function Track({
  label,
  color,
  segments,
  duration,
  onSeek,
}: {
  label: string;
  color: string;
  segments: [number, number][];
  duration: number;
  onSeek(ms: number): void;
}) {
  return (
    <button className="perception-track" onClick={event => {
      const rect = event.currentTarget.getBoundingClientRect();
      onSeek(((event.clientX - rect.left) / rect.width) * duration);
    }}>
      <span>{label}</span>
      <div>
        {segments.map(([start, value], index) => (
          <i key={`${start}-${index}`} style={{ left: `${start / duration * 100}%`, height: `${Math.max(4, value * 100)}%`, background: color }} />
        ))}
      </div>
    </button>
  );
}
