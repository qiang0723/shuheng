"""淘沙 · 创始五条 + #2b 登记种子(切片1)。

红线:pap_json 逐字转录 spec v0.2 §6 冻结原文,一个数不改(LLM 不发明、不选终值)。
通用件(成本/基准/holdout/闸)取 §6 冻结常量(pap.py)。登记后冻结;#2 关闭(被 #2b 取代)。
台账 append-only:本脚本仅在**空台账**上跑一次(非空即拒,防重复种子)。

⚠ 待人裁标记(见 STATE / CONSTRUCTION-LOG):
  - #3 source_type:§6 记 "literature+platform"(复合),§4 CHECK 单值 → 文档打架。
    暂取 source_type='literature'(文献动机)+ platform 数据记 contamination_note。待人裁。
  - #2 关闭:以 status='closed' + result_json 记关闭原因表示(被 #2b 取代、未跑)。待确认编码。
  - data_class / crowding_prior:§6/开工令未给具体值 → 暂留 NULL(该二列非冻结、可后填)。待人给值。
"""
from __future__ import annotations

from . import ledger, pap as P

# §5 A股清洗(engine 预处理)逐字转录,作为各假设 cleaning 通用件
CLEANING_A = ("A股清洗(spec §5):估计期=事件日前250至前91交易日,不足者剔;ST 剔除;"
             "一字板事件日标注+事件窗顺延;停牌缺失按 modified_rank 口径;"
             "可交易时点=事件日 T+1 开盘,CAR 窗口起点=T+1(盘后披露前视规避)")
SNAP_REQ = "result 须记快照批次号(spec §9,可复现)"


def _founding():
    """返回创始条目列表(顺序即登记序;drawdown_rebuy 先 #2 后 #2b 保证 family_trial 1→2)。"""
    return [
        dict(  # #1
            family="radar_heat", title="雷达 heat_signal 升温标记",
            source_type="platform", verdict_power="full",
            contamination_note="platform 来源,沿雷达自产信号 A7 口径",
            pap=P.build_pap(
                event_def="heat_signal 升温标记(沿雷达 A7 口径)",
                window="A7 口径",
                pool={"universe": "雷达信号覆盖股池", "source_view": "v_signal_radar"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "v_signal_radar"}),
        ),
        dict(  # #2 原始版(登记后关闭,被 #2b 取代)
            family="drawdown_rebuy", title="回撤反抽(原始版)",
            source_type="human", verdict_power="full",
            contamination_note="§6:全参数来自人的事前直觉",
            _close="被 drawdown_rebuy trial 2(#2b)取代,未跑",
            pap=P.build_pap(
                event_def=("雷达股池(PIT)内收盘自60日高点回撤≥10%后,站上10日线且连续3日不破=进场;"
                           "破20日线=失效"),
                window={"event": "20/60日", "strategy": "按离场规则"},
                pool={"universe": "雷达股池(PIT)", "source": "qbase行情+雷达股池"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "qbase行情+雷达股池"},
                extra={"exit_rule": "策略版离场:成本−20%强平 或 收盘破20日线,先到先出"}),
        ),
        dict(  # #2b b1 全市场流动性池版(开工令已批参数)
            family="drawdown_rebuy", title="回撤反抽·b1 全市场流动性池版",
            source_type="human", verdict_power="full",
            contamination_note=("核心定义与 X=20% 来自人;池型与 N=120 为 LLM 建议、人批;"
                                "未触样本收益数据;效力 full"),
            pap=P.build_pap(
                event_def=("雷达股池(PIT)进出场原文继承 #2:收盘自60日高点回撤≥10%后,"
                           "站上10日线且连续3日不破=进场;破20日线=失效"),
                window={"event": "20/60日", "strategy": "按离场规则"},
                pool={"universe": "b1 全市场流动性池", "filter": "成交额前20%",
                      "listing_min": "上市满120交易日"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "qbase行情+全市场流动性池"},
                extra={"exit_rule": "策略版离场:成本−20%强平 或 收盘破20日线,先到先出",
                       "inherit_from": "drawdown_rebuy #2 事件定义/进出场冻结原文"}),
        ),
        dict(  # #3 ⚠ 挂起:source_type 文档打架(§4 单值 vs §6 literature+platform),待人裁后补登
            _hold="§4 source_type 单值 CHECK vs §6 'literature+platform' 打架,待人裁",
            family="holder_sell", title="减持计划首次预披露漂移",
            source_type="literature", verdict_power="full",
            contamination_note=("§6:惯例参数由 LLM 按文献惯例拟定、人批、未接触样本数据。"
                                "⚠ 源标注:§6 记 literature+platform,§4 单值 → 暂取 literature"
                                "(文献动机),platform 数据=stk_holdertrade;待人裁"),
            pap=P.build_pap(
                event_def=("减持计划首次预披露公告(巨潮自建采集,announcementTime 为时间戳金标准),"
                           "减持比例≥总股本1%;2024新规前历史样本用当时口径首次公告日。"
                           "stk_holdertrade 仅作实施结果辅助表(按 ts_code+ann_date 聚合,"
                           "无公告ID局限入 pap_json)"),
                window="后 5/20/60 日",
                pool={"universe": "全市场(减持预披露)",
                      "source": "巨潮预披露采集(Q2)+stk_holdertrade"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "巨潮预披露+stk_holdertrade"}),
        ),
        dict(  # #4
            family="forecast_drift", title="业绩预告漂移",
            source_type="literature", verdict_power="full",
            contamination_note="§6:惯例参数由 LLM 按文献惯例拟定、人批、未接触样本数据",
            pap=P.build_pap(
                event_def=("业绩预告,valid_time=first_ann_date(非 ann_date);"
                           "修正公告(ann_date≠first_ann_date)不进本假设;分预喜/预亏/扭亏三层"),
                window="T+1 起,后 20/60 日",
                pool={"universe": "全市场(业绩预告)", "source": "qbase forecast_snap(Q2)"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "forecast_snap Q2 batch#1"},
                extra={"layers": "预喜/预亏/扭亏(三层映射=taosha 附录C 冻结,污染标注在案)"}),
        ),
        dict(  # #5
            family="rv_resonance", title="观象 resonance 共振",
            source_type="platform", verdict_power="full",
            contamination_note=("§6:惯例参数由 LLM 按文献惯例拟定、人批、未接触样本数据;"
                                "§6 注:池为确定性函数,预期大概率 INSUFFICIENT(验证样本量闸)"),
            pap=P.build_pap(
                event_def="观象节点日度 resonance 进全池当日分布前10%",
                window="卡面 horizon_days",
                pool={"universe": "观象全池", "source_view": "v_judgment_rv"},
                cleaning=CLEANING_A,
                snapshot_batch_req={"note": SNAP_REQ, "source": "v_judgment_rv"}),
        ),
    ]


def main():
    conn = ledger.connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM experiment")
            if cur.fetchone()[0] != 0:
                raise SystemExit("台账非空,拒绝重复种子(append-only)。如需重来请人工重建 taosha 库。")
        for item in _founding():
            hold = item.pop("_hold", None)
            if hold:
                print(f"  ⏸ 挂起 {item['family']}(待人裁): {hold}")
                continue
            close_reason = item.pop("_close", None)
            exp_id = ledger.register(
                family=item["family"], title=item["title"],
                source_type=item["source_type"], verdict_power=item["verdict_power"],
                pap=item["pap"], contamination_note=item["contamination_note"], conn=conn)
            ledger.freeze(exp_id, conn=conn)                 # 登记即冻结
            if close_reason:
                ledger.close(exp_id, close_reason, conn=conn)  # #2 关闭
            print(f"  登记 exp_id={exp_id} {item['family']} "
                  f"[{'closed' if close_reason else 'frozen'}]")
        conn.commit()
        print("创始五条 + #2b 登记冻结完成。")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
