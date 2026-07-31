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

const familyLabels: Record<string, string> = {
  radar_heat: "雷达热度",
  drawdown_rebuy: "回撤再买入",
  holder_sell: "股东减持",
  forecast_drift: "业绩预告漂移",
  rv_resonance: "实现波动共振",
  synthetic_smoke: "合成冒烟验证",
  limit_open: "一字涨停开板",
  suspension_return: "停牌复牌",
  volume_drought_break: "缩量后放量",
  high_pullback: "新高回撤",
  st_removal: "撤销风险警示",
  limit_down_open: "一字跌停开板",
  ex_div_gap: "除权缺口",
  st_imposition: "实施风险警示（旧登记）",
  yearend_strength: "年末强势",
  earnings_flash_gap: "业绩快报偏离",
  audit_qualified: "审计意见",
  dividend_surprise: "分红超预期",
  earnings_revision: "业绩预告修正",
  goodwill_impair: "商誉减值",
  delist_warning_financial: "财务退市风险警示",
  buyback_announce: "回购公告",
  sox_spillover: "跨市场半导体传导",
  preannounced_exhaustion: "预喜预跑透支",
};

export function familyLabel(family: string) {
  return familyLabels[family] ?? "其他研究家族";
}

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
