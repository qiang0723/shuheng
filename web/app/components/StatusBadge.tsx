import { powerLabels, statusLabels, verdictLabel } from "../../lib/format";
import type { ExperimentStatus, Verdict, VerdictPower } from "../../lib/types";

export function StatusBadge({ status }: { status: ExperimentStatus }) {
  return <span className={`badge status-${status}`}>{statusLabels[status]}</span>;
}

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const tone = verdict === "SIG" ? "verdict-sig" : verdict === "NOT_SIG" ? "verdict-not" : "verdict-none";
  return <span className={`badge ${tone}`}>{verdictLabel(verdict)}</span>;
}

export function PowerBadge({ power }: { power: VerdictPower }) {
  return <span className={`badge power-${power}`}>{powerLabels[power]}</span>;
}
