import { number, percent, signedPercent } from "../../lib/format";
import type { CalibrationMetrics } from "../../lib/types";

export function MetricGrid({ metric }: { metric: CalibrationMetrics }) {
  const items = [
    ["候选事件", number(metric.events), "条", "规则生成的事件总数"],
    ["有效样本", number(metric.valid), "条", "通过覆盖、估计期和清洗门的样本"],
    ["主窗样本", number(metric.mainN), "条", "主检验窗五日数据完整的样本"],
    ["主窗累计异常收益", signedPercent(metric.caar, 3), "", "市场调整后的平均累计收益"],
    ["聚集校正统计量", `${metric.adjBmp >= 0 ? "+" : ""}${number(metric.adjBmp, 3)}`, "", "本研究的唯一统计判决依据"],
    ["平均相关系数", number(metric.rhoBar, 4), "", "样本聚集程度诊断"],
    ["基什有效样本量", number(metric.kishEffectiveN, 1), "", "按相关性折算的聚集风险诊断数，不是正式样本数"],
    ["清洗剔除率", percent(metric.rejectRatio, 1), "", "候选事件中未进入有效样本的比例"],
  ];
  return <div className="metric-grid">{items.map(([label, value, unit, note]) => <article key={label}><span>{label}</span><div><strong>{value}</strong><small>{unit}</small></div><p>{note}</p></article>)}</div>;
}
