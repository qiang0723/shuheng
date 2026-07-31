import type { Metadata } from "next";
import Link from "next/link";
import { CalibrationStrip } from "./components/CalibrationStrip";
import { FieldGuide } from "./components/FieldGuide";
import { StatCard } from "./components/StatCard";
import { calibrationExperiments, platformSummary } from "../lib/fixtures";

export const metadata: Metadata = {
  title: "通俗首页",
  description: "枢衡当前研究结论、证据强度与判断校准的中文总览。",
};

export default function Home() {
  return (
    <main className="page-stack">
      <section className="hero-panel">
        <div className="eyebrow">当前研究结论</div>
        <div className="hero-grid">
          <div>
            <h1>工程流水线已成熟，尚未建立可依赖的超额收益证据。</h1>
            <p className="hero-copy">
              十条密封方向判断为五命中、五未命中。唯一统计显著结果来自预筛选实验，
              不能单独作为可交易策略或足额研究证据。
            </p>
          </div>
          <div className="hero-verdict">
            <span>当前固定读法</span>
            <strong>继续验证假设质量</strong>
            <small>不把“不显著”改写成“无效”</small>
          </div>
        </div>
      </section>

      <section className="stat-grid" aria-label="研究概况">
        <StatCard label="正式真实研究" value={platformSummary.realStudies} unit="条" note="不含合成冒烟测试" />
        <StatCard label="统计显著" value={platformSummary.significantStudies} unit="条" note="仅为智能预筛选效力" tone="warning" />
        <StatCard label="人提出·足额判决" value={platformSummary.humanFullStudies} unit="条" note="统计显著0条" />
        <StatCard label="方向校准" value={`${platformSummary.directionHits} / ${platformSummary.calibrationCount}`} note="五命中·五未命中" tone="neutral" />
      </section>

      <section className="content-grid">
        <article className="panel panel-large">
          <div className="section-heading">
            <div>
              <span className="eyebrow">判断校准</span>
              <h2>密封方向与正式结果</h2>
            </div>
            <Link className="text-link" href="/experiments">查看全部实验</Link>
          </div>
          <CalibrationStrip experiments={calibrationExperiments} />
        </article>

        <aside className="panel reading-panel">
          <span className="eyebrow">阅读约束</span>
          <h2>三种语义不得混用</h2>
          <ol className="rule-list">
            <li><strong>生命周期</strong><span>记录实验在登记、冻结或闭卷的哪一步。</span></li>
            <li><strong>统计判决</strong><span>只由预注册的聚集校正统计量决定。</span></li>
            <li><strong>证据效力</strong><span>说明结果是预筛选，还是可进入足额判决的人类假设。</span></li>
          </ol>
        </aside>
      </section>

      <FieldGuide compact />
    </main>
  );
}
