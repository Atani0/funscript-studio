import type { PerceptionTimeline } from '../core/perceptionTypes';

interface Props {
  perception?: PerceptionTimeline | null;
  currentTimeMs: number;
  enabled: boolean;
}

export function PerceptionOverlay({ perception, currentTimeMs, enabled }: Props) {
  if (!enabled || !perception?.segments?.length) return null;
  const segment = nearestSegment(perception, currentTimeMs);
  if (!segment) return null;

  return (
    <div className="perception-overlay">
      <div className="overlay-card">
        <strong>{shotLabel(segment.shot_type)}</strong>
        <span>风格：{styleLabel(segment.style)}</span>
        <span>置信度：{segment.confidence.toFixed(2)}</span>
        <span>视觉运动：{segment.visual.motion_intensity.toFixed(2)}</span>
        <span>互动强度：{segment.interaction.interaction_intensity.toFixed(2)}</span>
        <span>建议强度：{segment.suggested_motion.intensity.toFixed(2)}</span>
      </div>
      <div className="motion-region" style={{
        left: `${35 + segment.visual.motion_intensity * 10}%`,
        top: `${30 + segment.suggested_motion.intensity * 25}%`,
        width: `${18 + segment.visual.motion_intensity * 18}%`,
        height: `${18 + segment.visual.body_motion_overall * 18}%`,
      }} />
    </div>
  );
}

function nearestSegment(perception: PerceptionTimeline, ms: number) {
  return perception.segments.find(segment => ms >= segment.start && ms <= segment.end)
    ?? perception.segments.reduce((best, segment) =>
      Math.abs(segment.start - ms) < Math.abs(best.start - ms) ? segment : best,
    perception.segments[0]);
}

function styleLabel(style: string) {
  return ({
    live_action: '真人实拍',
    anime_2d: '二次元动画',
    animation_3d: '三维动画',
    mixed: '混合',
    unknown: '未知',
  } as Record<string, string>)[style] ?? style;
}

function shotLabel(shot: string) {
  return ({
    full_body: '全身镜头',
    upper_body: '上半身',
    lower_body: '下半身',
    hand_closeup: '手部特写',
    torso_closeup: '躯干特写',
    face_closeup: '脸部特写',
    wide_scene: '远景',
    unknown: '未知镜头',
  } as Record<string, string>)[shot] ?? shot;
}
