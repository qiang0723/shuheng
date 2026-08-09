import type { CalibrationMetrics, Experiment } from "./types";

const metrics: Record<number, CalibrationMetrics> = {
  8: { order: 1, predictedDirection: "negative", confidence: 0.6, directionHit: true, events: 6005, valid: 3742, mainN: 3618, caar: -0.014817818164073395, adjBmp: -0.4725876556124154, rhoBar: 0.06910608539908683, kishEffectiveN: 14.418601371806012, kpEffectiveN: 13.422188274070596, rejectRatio: 0.3768526228143214, industryUnknownRatio: 0.1557990379476216 },
  20: { order: 2, predictedDirection: "negative", confidence: 0.55, directionHit: false, events: 4892, valid: 3335, mainN: 3282, caar: 0.00698934637496006, adjBmp: 0.6072938553928457, rhoBar: 0.021716113386233696, kishEffectiveN: 45.43502515724997, kpEffectiveN: 44.448352999228746, rejectRatio: 0.31827473426001635, industryUnknownRatio: 0.06716641679160419 },
  13: { order: 3, predictedDirection: "positive", confidence: 0.7, directionHit: false, events: 2794, valid: 2124, mainN: 2036, caar: -0.044783531272772986, adjBmp: -1.4437154277206525, rhoBar: 0.07877961411792446, kishEffectiveN: 12.62413729266282, kpEffectiveN: 11.629612628175144, rejectRatio: 0.23979957050823192, industryUnknownRatio: 0.268361581920904 },
  12: { order: 4, predictedDirection: "positive", confidence: 0.7, directionHit: true, events: 641, valid: 473, mainN: 463, caar: 0.017953489818958123, adjBmp: 0.24556225505262455, rhoBar: 0.1288951043845724, kishEffectiveN: 7.64895788347071, kpEffectiveN: 6.663044658647555, rejectRatio: 0.2620904836193448, industryUnknownRatio: 0.12684989429175475 },
  11: { order: 5, predictedDirection: "positive", confidence: 0.6, directionHit: false, events: 42784, valid: 39290, mainN: 38888, caar: -0.004117936425822161, adjBmp: -0.10954785067298213, rhoBar: 0.09699720370526861, kishEffectiveN: 10.307133327286861, kpEffectiveN: 9.307370216322653, rejectRatio: 0.08166604338070306, industryUnknownRatio: 0.04418427080682107 },
  24: { order: 6, predictedDirection: "positive", confidence: 0.6, directionHit: true, events: 19258, valid: 13703, mainN: 13656, caar: 0.0033051753367197385, adjBmp: 0.5646755577681967, rhoBar: 0.006340770520612997, kishEffectiveN: 155.9263429006248, kpEffectiveN: 154.9376497421735, rejectRatio: 0.2884515526015162, industryUnknownRatio: 0.0020433481719331534 },
  10: { order: 7, predictedDirection: "positive", confidence: 0.6, directionHit: false, events: 13889, valid: 11432, mainN: 11312, caar: -0.006845906033937132, adjBmp: -0.30977878394328606, rhoBar: 0.09654697718430001, kishEffectiveN: 10.349180778326598, kpEffectiveN: 9.349998657845303, rejectRatio: 0.17690258477932178, industryUnknownRatio: 0.05432120363890833 },
  568: { order: 8, predictedDirection: "negative", confidence: 0.6, directionHit: true, events: 765, valid: 565, mainN: 554, caar: -0.15929536336562053, adjBmp: -5.522936355365047, rhoBar: 0.042969464364672125, kishEffectiveN: 22.38973539618494, kpEffectiveN: 21.427660458944132, rejectRatio: 0.26143790849673204, industryUnknownRatio: 0.3168141592920354 },
  16: { order: 9, predictedDirection: "positive", confidence: 0.5, directionHit: false, events: 7751, valid: 6942, mainN: 6881, caar: -0.0031967252693485917, adjBmp: -0.11178944002480809, rhoBar: 0.12220364037830078, kishEffectiveN: 8.174603811028497, kpEffectiveN: 7.175637466670484, rejectRatio: 0.1043736292091343, industryUnknownRatio: 0.04811293575338519 },
  17: { order: 10, predictedDirection: "positive", confidence: 0.8, directionHit: true, events: 2529, valid: 1841, mainN: 1822, caar: 0.001648578486047189, adjBmp: 0.2783298113335189, rhoBar: 0.009815666688264883, kishEffectiveN: 96.58552739379029, kpEffectiveN: 95.63747604998257, rejectRatio: 0.2720442862791617, industryUnknownRatio: 0.09397066811515481 },
  19: { order: 11, predictedDirection: "positive", confidence: 0.6, directionHit: false, events: 5055, valid: 3810, mainN: 3805, caar: -0.002804575188488496, adjBmp: -0.21553616523859276, rhoBar: 0.02998195801586874, kishEffectiveN: 33.07254974439924, kpEffectiveN: 32.08096994648493, rejectRatio: 0.24629080118694363, industryUnknownRatio: 0.01627296587926509 },
  14: { order: 12, predictedDirection: "positive", confidence: 0.6, directionHit: false, events: 4035, valid: 3163, mainN: 3095, caar: -0.018488168100005337, adjBmp: -0.9132553766202723, rhoBar: 0.06601787166688029, kishEffectiveN: 15.079964080903466, kpEffectiveN: 14.084416947469217, rejectRatio: 0.2161090458488228, industryUnknownRatio: 0.06038570976920645 },
};

const rows: Omit<Experiment, "metrics">[] = [
  { id: 1, family: "radar_heat", name: "雷达热度", status: "frozen", sourceType: "platform", verdictPower: "full", familyTrial: 1, verdict: null },
  { id: 2, family: "drawdown_rebuy", name: "回撤再买入（首轮）", status: "closed", sourceType: "human", verdictPower: "full", familyTrial: 1, verdict: null },
  { id: 3, family: "drawdown_rebuy", name: "回撤再买入（第二轮）", status: "done", sourceType: "human", verdictPower: "full", familyTrial: 2, verdict: "NOT_SIG" },
  { id: 4, family: "holder_sell", name: "大股东减持预披露", status: "done", sourceType: "literature", verdictPower: "full", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 5, family: "forecast_drift", name: "业绩预告漂移", status: "done", sourceType: "literature", verdictPower: "full", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 6, family: "rv_resonance", name: "实现波动共振", status: "frozen", sourceType: "platform", verdictPower: "full", familyTrial: 1, verdict: null },
  { id: 7, family: "synthetic_smoke", name: "合成冒烟测试", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "SIG" },
  { id: 8, family: "limit_open", name: "一字涨停开板", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 9, family: "suspension_return", name: "停牌复牌", status: "registered", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 10, family: "volume_drought_break", name: "缩量后放量收阳", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 11, family: "high_pullback", name: "新高后小幅回撤", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 12, family: "st_removal", name: "撤销ST风险警示", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 13, family: "limit_down_open", name: "一字跌停开板", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 14, family: "ex_div_gap", name: "除权缺口", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 15, family: "st_imposition", name: "实施ST（旧登记）", status: "closed", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 16, family: "yearend_strength", name: "年末强势股", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 17, family: "earnings_flash_gap", name: "业绩快报偏离预告", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 18, family: "audit_qualified", name: "审计意见事件", status: "registered", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 19, family: "dividend_surprise", name: "分红超预期", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 20, family: "earnings_revision", name: "业绩预告修正", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 21, family: "goodwill_impair", name: "商誉减值", status: "registered", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 22, family: "delist_warning_financial", name: "财务退市风险警示", status: "registered", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 23, family: "buyback_announce", name: "回购公告", status: "registered", sourceType: "llm", verdictPower: "prescreen", familyTrial: 1, verdict: null },
  { id: 24, family: "sox_spillover", name: "费城半导体指数跨市场传导", status: "done", sourceType: "human", verdictPower: "full", familyTrial: 1, verdict: "NOT_SIG" },
  { id: 25, family: "preannounced_exhaustion", name: "强预喜预跑透支", status: "registered", sourceType: "human", verdictPower: "full", familyTrial: 1, verdict: null },
  { id: 568, family: "delist_warning_financial", name: "实施ST风险警示", status: "done", sourceType: "llm", verdictPower: "prescreen", familyTrial: 2, verdict: "SIG" },
];

export const experiments: Experiment[] = rows.map((row) => ({ ...row, metrics: metrics[row.id] }));
export const calibrationExperiments = experiments.filter((row) => row.metrics).sort((a, b) => (a.metrics?.order ?? 0) - (b.metrics?.order ?? 0));
export const platformSummary = {
  ledgerRows: experiments.length,
  realStudies: 15,
  significantStudies: 1,
  humanFullStudies: 4,
  calibrationCount: calibrationExperiments.length,
  directionHits: calibrationExperiments.filter((row) => row.metrics?.directionHit).length,
};

export function getExperiment(id: number) {
  return experiments.find((row) => row.id === id);
}
