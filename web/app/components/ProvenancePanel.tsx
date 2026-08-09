import type { Experiment } from "../../lib/types";
import { familyLabel } from "../../lib/format";

const snapshotTime = "2026-08-09 22:14:05.537694（UTC+8）";
const ledgerSource = "docs/web-snapshot-2026-08-09/ledger_snapshot.csv";
const resultSource = "docs/web-snapshot-2026-08-09/calibration_results.csv";
const validationSource = "docs/web-snapshot-2026-08-09/validation.md";

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
