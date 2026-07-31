import type { Experiment } from "../../lib/types";
import { familyLabel } from "../../lib/format";

const snapshotTime = "2026-07-31 10:57:18（UTC+8）";
const ledgerSource = "taosha/docs/stage-review-10-experiments-2026-07-31/ledger_snapshot.csv";
const resultSource = "taosha/docs/stage-review-10-experiments-2026-07-31/calibration_results.csv";
const validationSource = "taosha/docs/stage-review-10-experiments-2026-07-31/validation.md";

export function ProvenancePanel({ experiment }: { experiment: Experiment }) {
  return (
    <section className="panel provenance-panel">
      <div className="section-heading">
        <div><span className="eyebrow">再追溯</span><h2>来源与快照</h2></div>
        <span className="snapshot-label">静态只读快照</span>
      </div>
      <dl className="provenance-list">
        <div><dt>数据截止时点</dt><dd>{snapshotTime}</dd></div>
        <div><dt>台账身份与生命周期</dt><dd><code>{ledgerSource}</code></dd></div>
        <div><dt>正式统计结果</dt><dd>{experiment.metrics ? <code>{resultSource}</code> : "当前快照无正式统计结果"}</dd></div>
        <div><dt>边界验证记录</dt><dd><code>{validationSource}</code></dd></div>
        <div><dt>研究家族</dt><dd>{familyLabel(experiment.family)}</dd></div>
        <div><dt>内部家族标识</dt><dd><code>{experiment.family}</code><small>仅用于机器追溯，不作为中文结论</small></dd></div>
      </dl>
    </section>
  );
}
