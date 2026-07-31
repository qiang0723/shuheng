import type { Metadata } from "next";
import { ExperimentLedger } from "../components/ExperimentLedger";
import { FieldGuide } from "../components/FieldGuide";
import { experiments } from "../../lib/fixtures";

export const metadata: Metadata = { title: "实验台账", description: "枢衡实验生命周期、统计判决与证据效力的26行只读快照。" };

export default function ExperimentsPage() {
  return (
    <main className="page-stack">
      <header className="page-heading"><div><span className="eyebrow">全量只读快照</span><h1>实验台账</h1><p>先看流程位置，再看统计判决，最后看证据效力。三者不可互相代替。</p></div><div className="page-count"><strong>26</strong><span>行台账</span></div></header>
      <ExperimentLedger experiments={experiments} />
      <FieldGuide />
    </main>
  );
}
