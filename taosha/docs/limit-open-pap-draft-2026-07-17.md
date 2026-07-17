# exp8(limit_open · 连续一字涨停开板)PAP 草案(2026-07-17,交人复核)

> **性质:草案,非冻结。** 依人冻结前裁决(`limit-open-prefreeze-rulings-2026-07-17.md`,原文即口径)转录。
> 冻结流程(密封甲案):人复核本草案 → 人批准冻结之**批复句内直接携带方向与把握度预判** → 批复句原文入
> F 条留痕 commit(时间戳先于一切结果)→ 方可登记冻结/生成 manifest/运行。批复前禁读任何收益。
> 结构预验:本草案 pap_json 已过 `pap.validate_pap` 层①(schema v2 / analysis_type=event),
> `parse_test_windows` → (5,20,60) = 主[0,+4]/次级[0,+19]/稳健[0,+59],与裁决三.2 逐项对应。

## §1 pap_json 草案全文

```json
{
  "pap_schema_version": 2,
  "analysis_type": "event",
  "event_def": "连续一字涨停链开板(冻结前裁决2026-07-17一):链=个股自身真实交易行序上连续≥2个一字涨停交易日,链成员唯一判据=limit_status='one_word' 且 open_limit_status='open_at_up_limit'(qbase explore_reader_prices_snap 实源,PIT板块制度价位;不新增事实源或代理规则);停牌缺bar不计交易日、不重置链;禁跨任何有真实bar但非一字涨停的交易日拼接;每段取最大饱和链,不重复截取子链。事件日=链后首个 limit_status!='one_word' 的真实交易行(链后一字跌停等一字状态继续顺延;停牌日不得为事件日)。每(ts_code,event_date)唯一,重复映射fail-closed剔除并上报。研究期 2007-01-01≤event_date<2024-07-01(2007前qbase退市实体覆盖缺口,防幸存者偏差);全A股、排除北交所(视图DDL焊死);ST链保留;新股连板保留,链起点上市交易龄≤30(自身真实交易行序号,上市首bar=第1行)标记recent_listing、其余seasoned,仅预注册异质性报告,不产独立verdict、不改主样本主判决。此前6,841形态近似计数永久作废,冻结依据仅本次实源口径。",
  "window": "T+1起,后5/20/60日",
  "pool": {
    "universe": "全A股(排除北交所),全市场价量宇宙(事件由价量实源生成,无外部公告表)",
    "source": "qbase explore_reader_prices_snap(limit_status/open_limit_status)+ explore_reader_listing_snap(PIT上市区间)+ explore_reader_calendar_snap"
  },
  "benchmark": {
    "pool_hypothesis": "雷达股池等权",
    "market_hypothesis": "全市场等权"
  },
  "cost": {
    "commission": 0.00025,
    "stamp_tax_sell": 0.001,
    "slippage_oneway": 0.001,
    "limit_up_board_untradeable": true
  },
  "holdout": {
    "holdout_start": "2024-07-01",
    "use_requires_human_approval": true,
    "once_per_hypothesis": true
  },
  "cleaning": "A股清洗(spec §5):估计期=事件日前250至前91交易日(160日),窗内有效交易日<112(70%)剔;停牌=轴内缺bar或flag,事件日T或T+1停牌剔(item7);一字板T+1顺延(τ=0=首个可交易日,顺延超5交易日剔postpone);ST处置=复核点C2待人裁(甲=spec§5照剔+分层计数留痕/乙=保留入主样本+ST/非ST分层CAR报告);CAR轴起点=T+1(事件定义需完整观察事件日全日状态,裁决三.1)",
  "snapshot_batch_req": {
    "source": "qbase daily/adj_factor/stock_basic/namechange/trade_cal + taosha market_eqw_return(全部经 StudySnapshot manifest 路由)",
    "note": "result 须记 manifest ID+digest(硬化②);manifest 于冻结后另行生成,本草案不产生"
  },
  "sample_gate": 30,
  "layers": ["recent_listing", "seasoned"],
  "verdict_authority": "唯一判决=顶层主窗[0,+4] ADJ-BMP(裁决三.2/三.4);次级窗[0,+19]、稳健窗[0,+59]、朴素t/Corrado秩/日历时间法、ST分层、recent_listing/seasoned分层、板块/创业板regime分布,均为报告项,不判决、不得择优改判",
  "reporting_commitments": "2015年事件集中及相关折算N(ρ̄→N_eff)必须在结果中如实报告,不因此另调参数(裁决三.6);剔除分解逐年逐因报告(承exp4范式)",
  "verdict_power_note": "exp8=llm/prescreen效力,不得写成full证据(裁决三.5);报告强制水印(铁律①)"
}
```

窗口语义钉死:`后5/20/60日` = τ∈[0,+4]/[0,+19]/[0,+59],τ=0:=T+1(S2-DEC3);runner 消费=首窗主
(唯一进 verdict)/中窗次级报告/末窗稳健(人裁 2026-07-15 三窗判点①固定角色,不得择优改判)。
基准=全市场等权**单跑**(pool_hypothesis 无冻结定义不运行,承 exp4 人裁② 2026-07-15 先例;
benchmark 键保留 §6 冻结双句结构原文)。

## §2 复核点(冻结批复前须人裁;C1/C2 系字面与实物打架上报,工地不自裁)

- **C1 · τ=0 锚定:裁决三.1 字面 vs 引擎冻结实物。** 裁决字面="CAR轴从事件日后下一交易日T+1开始";
  引擎实物(S2-DEC3,冻结)=τ=0=事件日后**首个可交易日**——若 T+1 本身又一字(开板后再封)或停牌,
  顺延,超 5 交易日剔(postpone)。开板日样本中再封形态真实存在,两读法在此类事件上不同。
  **建议=按实物转录**(一字再封日实际不可成交,顺延即冻结成本口径 limit_up_board_untradeable 的既有语义;
  exp4 判例:实物即冻结设计)。若人要求字面"下一交易日不顺延",须改主干统计口径,不建议。
- **C2 · ST 处置(文档打架,四类必报①④)。** 裁决二.4"ST链保留;ST与非ST作为报告分层,不分别产生判决"
  vs 引擎 cleaning **spec §5 ST 硬剔除**(冻结口径,exp4 即按此剔 4,239 事件)。两案:
  **甲**=生成器保留 ST 链、清洗按 spec §5 照剔、分层=ST已剔除层计数留痕(引擎零改动;"分层报告"退化为
  剔除计数,无 ST 层 CAR);**乙**=ST 事件入主样本与主判决,ST/非ST 各出分层统计(需最小适配:cleaning/runner
  加 `st_policy` 参数,默认 reject 零回归、exp8 显式 keep,施工范式承硬化③ st_mode 先例+合成 e2e 逐字节不变证)。
  裁决字面倾向乙;乙=对 spec §5 开 exp8 单点例外,属动统计口径,须人明示。
- **C3 · recent_listing 层结构性无 CAR。** 覆盖门槛(冻结口径③:估计窗 160 日内有效≥112)决定
  链起点交易龄≤30 的事件**必然** coverage 剔除(该票历史 bar 远少于 112)→ recent_listing 异质性报告
  只能=事件计数+剔除分解,层内 CAR 为 INSUFFICIENT/空。窄闸计此类链 1,528 条(23.4%),即主样本预期
  折损中最大一块,且 len5+ 长链中 66.4% 落此类(长链效应主要由新股贡献——主窗结论的适用域将以 seasoned 为主)。
  **建议=甲:如实预注册**(本节文字即预注册披露);乙=为该层另定估计口径,属动口径+主干改动,不建议。
- **C4 · 重复映射 fail-closed 操作化。** 现实现=同(ts_code,event_date) 多链时**涉事链全部剔除**、逐条上报
  (不猜不合并);备选=合并为一事件(保最早链几何)。窄闸计自身行序口径共享事件日 74 处(≈1%量级),
  形态=链—一字跌停—再封链夹层。请人钉一案。
- **C5 · recent_listing 交易龄操作化。** 现实现="链起点行在该票自身真实交易行序中的序号≤30"(停牌稳健,
  与连续性同轴);备选=日历日 `chain_start_date−list_date≤30`。窄闸预估 1,528 系近似口径,冻结后以生成器
  实跑计数为准。请人钉一案。
- **C6 · 分层块显著性字段标注。** runner 实物 type_strata/board_strata 层内含检验统计字段;本 PAP 以
  `verdict_authority` 键声明唯一判决=顶层主窗。若人要求结构上再加 NOT_FOR_VERDICT 字样标注(承 exp4
  敏感性块范式),属渲染层最小适配,冻结批复句注明即可。

## §3 数据基础(2026-07-17 准确性窄闸实源计数;报告基线)

自身行序口径 up 链 6,484(日历连续口径 6,537:len2=3,091/len3=1,167/len4=573/len5+=1,706;年峰 2015=1,418);
共享事件日 74;开板日=日历次日 95.4%(6,238);停牌缺口后开板 152;停牌后复板(缺口跨链)121;
链尾接一字跌停 26;混 ST 链 0;IPO≤30 日链 1,528=23.4%(上市首日 44% 规则不产 one_word 链,从第 2 日起计);
1996-12-16 制度前链 0。**最终事件数以冻结后生成器实跑为准**(本裁决叠加事件日顺延/范围/唯一性后
计数会低于链数);6,841 形态近似数永久作废不再引用。

## §4 fixture 验证实录(授权三,已毕)

`taosha/compute/limit_open_rules.py`(纯函数零 I/O,裁决参数全常量化)+
`taosha/harness/verify_limit_open_rules.py` = **33/33 PASS**(零 DB/零真实数据/零收益):
①连续性 7 例(含双条件判据/触板未一字断链/N=2 门)②停牌 3 例(缺 bar 不计不重置/复牌 bar=事件日)
③反向一字顺延 4 例(一字跌停 1/2 行顺延/开盘位异常行同顺延/顺延至边界 right_censored)
④最大饱和链 2 例(五连板恰 1 链 1 事件+确定性双跑)⑤唯一事件 3 例(上下上夹层两链同事件日全剔逐条上报)
+范围 4 例(2007 下界/跨年链按 event_date 判/holdout 再挡一道/制度前诊断)+事件日形态 2 例
(开板日=触板未一字/触跌停未一字均合法)+recent_listing 边界 3 例+跨票聚合 3 例+空输入退化 2 例。
