import Link from "next/link";
import { researchReadiness } from "../../lib/fixtures";

export function ResearchReadiness() {
  return (
    <section className="panel readiness-panel" aria-labelledby="readiness-title">
      <div className="section-heading readiness-heading">
        <div>
          <span className="eyebrow">个股输出就绪度</span>
          <h2 id="readiness-title">现在能给出股票吗？</h2>
        </div>
        <span className="readiness-status">{researchReadiness.status}</span>
      </div>

      <div className="readiness-grid">
        <div className="readiness-answer">
          <strong>{researchReadiness.headline}</strong>
          <p>{researchReadiness.explanation}</p>
          <ul>
            {researchReadiness.requirements.map((requirement) => <li key={requirement}>{requirement}</li>)}
          </ul>
          <Link className="text-link" href="/experiments">查看研究证据与生命周期 →</Link>
        </div>

        <div className="gate-grid" aria-label="当前研究停点">
          {researchReadiness.gates.map((gate) => (
            <article key={gate.id} className="gate-card">
              <div><span>实验 {gate.id}</span><strong>{gate.name}</strong></div>
              <em>{gate.status}</em>
              <p>{gate.reason}</p>
            </article>
          ))}
        </div>
      </div>

      <p className="readiness-source">
        研究结果快照：{researchReadiness.resultSnapshot}；研发状态：{researchReadiness.statusSnapshot}。
        两类时点独立，不把后续施工状态冒充为结果重算。
      </p>
    </section>
  );
}
