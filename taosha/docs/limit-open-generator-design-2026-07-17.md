# exp8 事件生成器最小适配设计(2026-07-17,授权二;设计+fixture,不施工 driver、不运行)

> 口径出处=冻结前裁决(`limit-open-prefreeze-rulings-2026-07-17.md`)。设计原则=宪章⑤:复用主干只加
> 适配器不 fork;裁决四.3:零 qbase 新对象,直接消费现有 StudySnapshot 视图。
> 本单元已施工实物=规则纯函数+fixture(§4);driver 与(如人裁 C2 选乙)st_policy 适配在冻结令后施工。

## §1 数据流(全链,冻结后形态)

```
ViewReader(snapshot_id=M, sample=listing()全A键集)          ← 视图零改动;sample显式给全宇宙
  └ prices()  流式(服务器游标,ts_code,trade_date 升序;holdout/.BJ/∩calendar 视图焊死)
      → driver: itertools.groupby(ts_code) 逐票
      → PriceRow → dict 最小映射 {trade_date, limit_status, open_limit_status}
      → compute.limit_open_rules.select_limit_open_events(纯函数,已建+fixture 33/33)
      → merge_selections → selection(events/rejects/counters/reject_reasons 全量入 audit)
  → EventRow(ts_code, event_id=f"{ts}:{yyyymmdd}", first_ann_date=event_date,
             event_type_layer='recent_listing'|'seasoned', snapshot_batch=manifest批)
  → ViewReader(snapshot_id=M, sample=事件票集合)             ← 承 exp4 两次构造范式
  → runner.run_study(reader, pap, benchmark_mode='market', events=events,
                     strata_enabled=True[layers=recent/seasoned], st_mode='event_day'
                     [, st_policy=人裁C2])
  → report.render;audit 增 limit_open_selection 块(计数/剔除/重复映射清单/链长分布/逐年分布)
```

## §2 触碰面清单(最小化)

| 面 | 动作 | 状态 |
|---|---|---|
| `taosha/compute/limit_open_rules.py` | 新增,纯函数零 I/O,裁决参数全常量化 | ✅ 已建 |
| `taosha/harness/verify_limit_open_rules.py` | 新增,构造 fixture 33/33 | ✅ 已建全绿 |
| `taosha/harness/run_limit_open_study.py` | 新增 driver(承 run_holder_sell_study 范式,§1 数据流) | ⏳ 冻结令后 |
| `taosha/reader/view.py` | **零改动**(sample=listing 键集即得全宇宙 prices 流) | — |
| `taosha/engine/cleaning.py`+`runner.py` | 仅当 C2 选乙:`st_policy` 参数('reject' 默认零回归/'keep');承硬化③ st_mode 穿线先例;验收=既有全家福+合成 e2e 逐字节不变 | ⏳ 待人裁 |
| `taosha/engine/report.py` | 仅当 C6 要求 NOT_FOR_VERDICT 渲染标注 | ⏳ 待人裁 |
| qbase 一切对象 / 台账 / manifest | **零写入零新增**(裁决四.3;manifest 冻结后另行) | — |

engine/runner 既有能力直接复用、零改动:三窗(5,20,60)固定角色、ADJ-BMP 权威+三辅助法、
type_strata(event_type_layer=recent/seasoned 层报告)、board_strata+创业板 regime 审计字段(裁决二.6)、
剔除逐年分解、ρ̄/N_eff 折算报告(裁决三.6)、sample_gate=30、聚集警示(2015 峰承 exp4 朴素 t 注记范式)。

## §3 性能与确定性

全宇宙 prices 流 ≈ bar_daily 全量(~1.7–2 千万行,服务器游标 itersize=100k,逐票分组处理,
单票峰值内存 ~1 万行);链检测 O(n) 单遍;生成器整体预算=分钟级。确定性=行序 (ts_code,trade_date)
由 SQL ORDER BY 钉死 + 纯函数 → 双跑逐字节同(施工后以双跑 sha 验收,承既有范式)。
事件研究段与 exp4 同量级(事件数≲6.5k<exp4 12k)。

## §4 fixture 实录(授权三)

`verify_limit_open_rules.py` 33/33 PASS,五性质+边界全覆盖,明细见 PAP 草案档 §4。
零 DB/零真实数据/零收益读取;纯函数双跑确定性在册。

## §5 冻结后施工序(预排,届时按人令)

1. 人批复句(内嵌方向+把握度预判,密封甲案)F 条留痕 commit → 台账 exp8 冻结(状态机,pap_json=§1 终版);
2. driver 施工+(C2 乙则 st_policy 适配+全家福回归+合成 e2e 逐字节证);
3. 研究 manifest(绑现行源快照;qbase 源无刷新则直接 `--create`,再种序不预期触发);
4. §7 单次正式运行 → 交付 → 人验收 → persist 另令。
