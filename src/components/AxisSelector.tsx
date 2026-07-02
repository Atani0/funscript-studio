import type { AxisName } from '../core/types';

interface Props {
  active: AxisName;
  counts: Record<AxisName, number>;
  onChange(axis: AxisName): void;
}

const axes: { id: AxisName; label: string; hint: string }[] = [
  { id: 'stroke', label: '升降', hint: '主轴' },
  { id: 'surge', label: '前后', hint: '多轴' },
  { id: 'sway', label: '左右', hint: '多轴' },
  { id: 'twist', label: '旋转', hint: '多轴' },
  { id: 'roll', label: '侧倾', hint: '多轴' },
  { id: 'pitch', label: '俯仰', hint: '多轴' }
];

export function AxisSelector({ active, counts, onChange }: Props) {
  return (
    <div className="axis-selector" role="tablist">
      {axes.map(axis => (
        <button
          key={axis.id}
          className={active === axis.id ? 'axis-button active' : 'axis-button'}
          onClick={() => onChange(axis.id)}
          role="tab"
          aria-selected={active === axis.id}
        >
          <span>{axis.label}</span>
          <small>{axis.hint} · {counts[axis.id]}</small>
        </button>
      ))}
    </div>
  );
}
