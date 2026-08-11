import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { FieldGuide } from "../../components/FieldGuide";
import { MetricGrid } from "../../components/MetricGrid";
import { ProvenancePanel } from "../../components/ProvenancePanel";
import { PowerBadge, StatusBadge, VerdictBadge } from "../../components/StatusBadge";
import { getExperiment, getResearchGate, researchReadiness } from "../../../lib/fixtures";
import { familyLabel, percent, powerLabels, sourceLabels } from "../../../lib/format";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const experiment = getExperiment(Number(id));
  return { title: experiment ? experiment.name : "实验不存在" };
}

export default async function ExperimentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const experiment = getExperiment(Number(id));
  if (!experiment) notFound();
  const metric = experiment.metrics;
  const researchGate = getResearchGate(experiment.id);

  return (
    <main className="page-stack">
      <Link className="back-link" href="/experiments">← 返回实验台账</Link>
      <header className="detail-heading">
        <div><span className="eyebrow">实验 {experiment.id}·第{experiment.familyTrial}轮</span><h1>{experiment.name}</h1><p>所属研究家族：{familyLabel(experiment.family)}</p></div>
        <div className="badge-stack"><StatusBadge status={experiment.status} /><VerdictBadge verdict={experiment.verdict} /><PowerBadge power={experiment.verdictPower} /></div>
      </header>

      <section className="detail-grid">
        <article className="panel conclusion-card">
          <span className="eyebrow">正确读法</span>
          <h2>{experiment.verdict === "SIG" ? "聚集校正后达到统计显著。" : experiment.verdict === "NOT_SIG" ? "聚集校正后未达统计显著。" : "尚未形成正式统计判决。"}</h2>
          <p>{experiment.verdictPower === "prescreen" ? "本实验只具预筛选效力；即使显著，也只能进入人工选题候选池。" : "本实验具足额判决效力，但仍须区分统计证据与可交易性证据。"}</p>
        </article>
        <aside className="panel identity-card"><span className="eyebrow">身份与角色</span><dl><div><dt>假设来源</dt><dd>{sourceLabels[experiment.sourceType]}</dd></div><div><dt>证据效力</dt><dd>{powerLabels[experiment.verdictPower]}</dd></div><div><dt>家族轮次</dt><dd>第{experiment.familyTrial}轮</dd></div>{metric && <div><dt>密封方向</dt><dd>{metric.predictedDirection === "positive" ? "正" : "负"}·把握度{percent(metric.confidence, 0)}</dd></div>}</dl></aside>
      </section>

      {researchGate && (
        <section className="panel current-gate-panel" aria-labelledby="current-gate-title">
          <div className="section-heading">
            <div><span className="eyebrow">当前研究停点</span><h2 id="current-gate-title">该实验尚不能继续形成正式结果</h2></div>
            <span className="readiness-status">{researchGate.status}</span>
          </div>
          <p>{researchGate.reason}</p>
          <div className="gate-identity">
            <span>研发状态：{researchReadiness.statusSnapshot}</span>
            <span>研究结果快照：{researchReadiness.resultSnapshot}</span>
          </div>
          <small>两类时点独立；本段只解释研发停点，不构成统计结果、代理证据或恢复授权。</small>
        </section>
      )}

      {metric ? <section className="panel"><div className="section-heading"><div><span className="eyebrow">正式结果</span><h2>关键统计与样本</h2></div><span className={metric.directionHit ? "hit yes" : "hit no"}>{metric.directionHit ? "密封方向命中" : "密封方向未中"}</span></div><MetricGrid metric={metric} /></section> : <section className="panel empty-panel"><span className="empty-mark">—</span><h2>暂无详细统计快照</h2><p>本静态版只展示仓内fixture明确存在的字段，不使用猜测值填充。</p></section>}

      {experiment.id === 568 && <section className="boundary-callout"><strong>执行边界</strong><p>该结果包含一字跌停锁死价格观察，不得读作可成交收益或可执行策略。</p></section>}
      {experiment.id === 19 && <section className="boundary-callout"><strong>样本边界</strong><p>2024年剔除集中于稳健窗与数据右界的交互，不构成年度效应或事件质量差异；辅助统计均不进入正式判决。</p></section>}
      {experiment.id === 14 && <section className="boundary-callout"><strong>估计量边界</strong><p>主结果使用复权总回报，不能读作“名义价格幻觉”已经得到证实；辅助三法即使名义显著也不进入正式判决。</p></section>}
      {experiment.id === 7 && <section className="boundary-callout"><strong>样本边界</strong><p>这是合成冒烟测试，不属于正式真实研究，也不计入当前唯一真实显著结果。</p></section>}
      <ProvenancePanel experiment={experiment} />
      <FieldGuide />
    </main>
  );
}
