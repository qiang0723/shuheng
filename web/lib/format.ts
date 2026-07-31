import type { ExperimentStatus, SourceType, Verdict, VerdictPower } from "./types";

export const statusLabels: Record<ExperimentStatus, string> = {
  registered: "登记待排",
  frozen: "已冻结",
  done: "已闭卷",
  closed: "已关闭",
};

export const sourceLabels: Record<SourceType, string> = {
  human: "人提出",
  llm: "智能生成",
  literature: "文献来源",
  platform: "平台基线",
};

export const powerLabels: Record<VerdictPower, string> = {
  full: "足额判决",
  prescreen: "预筛选",
};

export function verdictLabel(verdict: Verdict) {
  if (verdict === "SIG") return "统计显著";
  if (verdict === "NOT_SIG") return "未达显著";
  return "尚无判决";
}

export function signedPercent(value: number, digits = 2) {
  return new Intl.NumberFormat("zh-CN", {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    signDisplay: "always",
  }).format(value);
}

export function percent(value: number, digits = 1) {
  return new Intl.NumberFormat("zh-CN", {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function number(value: number, digits = 0) {
  return new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}
