"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { powerLabels, sourceLabels } from "../../lib/format";
import type { Experiment, ExperimentStatus } from "../../lib/types";
import { PowerBadge, StatusBadge, VerdictBadge } from "./StatusBadge";

const filters: { value: "all" | ExperimentStatus; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "registered", label: "登记待排" },
  { value: "frozen", label: "已冻结" },
  { value: "done", label: "已闭卷" },
  { value: "closed", label: "已关闭" },
];

export function ExperimentLedger({ experiments }: { experiments: Experiment[] }) {
  const [status, setStatus] = useState<"all" | ExperimentStatus>("all");
  const [query, setQuery] = useState("");
  const visible = useMemo(() => {
    const term = query.trim().toLowerCase();
    return experiments.filter((row) => {
      const statusMatch = status === "all" || row.status === status;
      const queryMatch = !term || row.name.includes(term) || String(row.id).includes(term) || row.family.toLowerCase().includes(term);
      return statusMatch && queryMatch;
    });
  }, [experiments, query, status]);

  return (
    <section className="panel ledger-panel">
      <div className="ledger-controls">
        <div className="filter-group" aria-label="按生命周期筛选">
          {filters.map((filter) => (
            <button key={filter.value} className={status === filter.value ? "filter active" : "filter"} onClick={() => setStatus(filter.value)}>{filter.label}</button>
          ))}
        </div>
        <label className="search-box"><span>搜索</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入实验名称或编号" /></label>
      </div>
      <div className="table-wrap">
        <table className="ledger-table">
          <thead><tr><th>编号</th><th>实验</th><th>生命周期</th><th>统计判决</th><th>证据效力</th><th>来源</th><th>家族轮次</th></tr></thead>
          <tbody>
            {visible.map((row) => (
              <tr key={row.id}>
                <td className="mono">{row.id}</td>
                <td>
                  <Link href={`/experiments/${row.id}`}>
                    <strong>{row.name}</strong>
                    {row.id === 7 && <small>合成冒烟·不计正式研究</small>}
                  </Link>
                </td>
                <td><StatusBadge status={row.status} /></td>
                <td><VerdictBadge verdict={row.verdict} /></td>
                <td><PowerBadge power={row.verdictPower} /><small className="cell-note">{powerLabels[row.verdictPower]}</small></td>
                <td>{sourceLabels[row.sourceType]}</td>
                <td>第{row.familyTrial}轮</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">当前显示 {visible.length} / {experiments.length} 条·数据快照 2026-08-09 22:14:05.537694（UTC+8）</div>
    </section>
  );
}
