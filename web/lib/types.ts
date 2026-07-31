export type ExperimentStatus = "registered" | "frozen" | "done" | "closed";
export type Verdict = "SIG" | "NOT_SIG" | null;
export type SourceType = "human" | "llm" | "literature" | "platform";
export type VerdictPower = "full" | "prescreen";

export interface CalibrationMetrics {
  order: number;
  predictedDirection: "positive" | "negative";
  confidence: number;
  directionHit: boolean;
  events: number;
  valid: number;
  mainN: number;
  caar: number;
  adjBmp: number;
  rhoBar: number;
  kishEffectiveN: number;
  kpEffectiveN: number;
  rejectRatio: number;
  industryUnknownRatio: number;
}

export interface Experiment {
  id: number;
  family: string;
  name: string;
  status: ExperimentStatus;
  sourceType: SourceType;
  verdictPower: VerdictPower;
  familyTrial: number;
  verdict: Verdict;
  metrics?: CalibrationMetrics;
}
