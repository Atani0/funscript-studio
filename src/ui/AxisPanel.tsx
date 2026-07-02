import { axes, axisDescription, axisDisplayName } from '../core/axis_manager';
import type { AxisName } from '../core/types';

interface Props {
  active: AxisName;
  counts: Record<AxisName, number>;
  locked: Record<AxisName, boolean>;
  onChange(axis: AxisName): void;
  onToggleLock(axis: AxisName): void;
}

export function AxisPanel({ active, counts, onChange }: Props) {
  return (
    <section className="axis-panel" aria-label="轴选择">
      {axes.map(axis => (
        <button
          key={axis}
          className={active === axis ? 'axis-button active' : 'axis-button'}
          onClick={() => onChange(axis)}
          title={axisDescription(axis)}
          type="button"
        >
          <span>{axisDisplayName(axis)}</span>
          <small>{counts[axis]} 个节点</small>
        </button>
      ))}
      <span
        className="axis-note"
        title="支持导入 MultiFunPlayer / OSR 多轴文件：主文件、.surge、.sway、.twist、.roll、.pitch。快速生成默认仍只生成主轴。"
      >
        支持多轴导入：前后 / 左右 / 旋转 / 侧倾 / 俯仰
      </span>
    </section>
  );
}
