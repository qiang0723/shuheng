# Q3-B 行情回填 · 验收(2026-07-07)

> 人拍 B(2026-07-07):marketdata=梯队4 公共事实,回填进 qbase 本地表(源 tushare,不碰老平台;
> 换源约束原"现在不迁移"经人批变更)。件=`007_marketdata_pit.sql` + `qbase/ingest/seed_marketdata.py`。
> 凭实物:库为唯一真身,以下均查库结果(aliyun-new qbase)。

## 回填终值(append-only 快照,流式 COPY)

| 源 | batch | 行数 | 去双发 |
|---|---|---|---|
| tushare:daily(未复权 OHLCV) | 3 | **17,138,664** | 0 |
| tushare:adj_factor(复权因子) | 4 | **17,680,484** | 0 |
| tushare:trade_cal(SSE 日历) | 5 | **13,162** | 0 |

宇宙锚 entity_master batch=6(5861 含退市)。表 = `bar_daily_snap`/`adj_factor_snap`/`trade_cal_snap`,
双时戳(valid=trade_date/cal_date,observed=pull_time)+ 冻结触发器(append-only)+ 无 UNIQUE(承 006 忠实存全)。

## V1–V5 验收(仿 Q2 三层核对协议)

- **V1 源口径**:3 batch 全 `tushare:*`,pull 2026-07-07,note 记分片范围。✓(源=tushare,非老机 md)
- **V2 去重**:daily 批内 `(ts_code,trade_date)` 重复键 = **0**;流式逐片整行去重,去双发 0(本次源无双投递)。✓
- **V3 退市宇宙(防幸存偏差)**:退市 D=334 中 **333 有行情**、在市 L=5527 **全有**。✓
- **V4 复权/日历完整**:bar 5860 票 / adj 5860 票(匹配);日历 **1990-12-19 → 2026-12-31、8797 交易日**。✓
- **V5 PIT**:双时戳齐(valid_time=trade_date、observed_time NOT NULL);样本 000001.SZ 近 3 日 close/pre_close 齐。✓
- 行情跨度:1990-12-19 → 2026-07-07。

## 唯一缺口(C1,预期内、在案不补)

宇宙 5861 中 **1 只无 tushare 行情** = **`T600018.SH` 上港集箱(退),退市 2006-10-20**。
= C1 已挂账「tushare 对 2007 前退市不完备」(Q1 同族 T00018.SH)。默认不捞、挂老机退役迁移单(≈2027 H1)。
对切片3(现代假设 + 2024-07-01 holdout)无影响。

## 归一列归属(铁律7:facts 零判断,归一是视图的活)

facts 只存原始 OHLCV/因子/日历。**后复权收盘(D3=close×adj_factor)/is_suspended(交易日无 bar)/
limit_status(close vs pre_close vs 板块限幅)/board(ts_code 前缀)/is_st(PIT 名称)/industry(entity_master)**
全部算在 Q3 explore_reader 视图(008 另件),此处不预置。

## 结论 / 下一步

行情回填达标(V1–V5 全过,唯一缺口=C1 预期内)。→ **008 explore_reader 视图**(holdout `<2024-07-01` 焊 WHERE
+ 引擎 role 仅 SELECT 视图、对底表零权 + 契约逐字段对齐 + 越权/泄漏实测三件套)→ Q3 验收 → 切片3 开工令。
