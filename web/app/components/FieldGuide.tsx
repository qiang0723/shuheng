const fields = [
  ["生命周期", "实验在登记、冻结、闭卷或关闭流程中的位置。不代表统计结论。"],
  ["统计判决", "只由预注册的主窗聚集校正统计量决定。“未达显著”不等于证明无效。"],
  ["证据效力", "“足额判决”可进入正式研究证据；“预筛选”只能帮助选择后续人类假设。"],
  ["主窗累计异常收益", "事件主检验窗内，个股收益扣除冻结基准后的平均累计值。单位为百分比。"],
  ["聚集校正统计量", "处理事件同日聚集和样本相关性后的唯一判决统计量。阈值受家族试验次数影响。"],
  ["基什有效样本量", "根据平均相关性折算的诊断值，用于提示聚集风险；不是正式样本数，也不直接替代主窗判决样本。"],
];

export function FieldGuide({ compact = false }: { compact?: boolean }) {
  const visible = compact ? fields.slice(0, 3) : fields;
  return (
    <section className="panel field-guide">
      <div className="section-heading"><div><span className="eyebrow">字段说明</span><h2>这些数字怎么读</h2></div></div>
      <div className="field-grid">
        {visible.map(([name, description]) => <div key={name}><strong>{name}</strong><p>{description}</p></div>)}
      </div>
    </section>
  );
}
