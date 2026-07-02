interface Props {
  onTrain(datasetName: string): Promise<void>;
}

export function TrainingDatasetPanel({ onTrain }: Props) {
  return (
    <section className="learning-card">
      <div className="perception-heading">
        <strong>训练集</strong>
        <span>第一版支持后端数据集、学习参数和相似片段索引</span>
      </div>
      <div className="learning-row">
        <button onClick={() => void onTrain('default')}>训练默认参数</button>
      </div>
      <small>样本导入接口已就绪；下一阶段可以把视频 + 脚本配对导入做成完整表单。</small>
    </section>
  );
}
