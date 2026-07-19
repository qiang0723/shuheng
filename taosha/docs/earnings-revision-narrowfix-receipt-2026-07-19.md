# exp20 三处窄修回执(2026-07-19,交外部复核闭合)

人令原文=`earnings-revision-narrowfix-order-2026-07-19.md`(留痕 commit `ad9870c` 先于施工)。

## 1. 三处窄修完成情况(commit `00cf8c1`,零生产逻辑改动)

| # | 令 | 实施 | 验证 |
|---|----|------|------|
| ① | 残差裁定落档 | −12=历史参考数血缘缺口(5,225 脚本未归档不可重放,丧失硬基线证据资格),非冻结规则或适配代码异常;provenance 异常留档=验收档 §11;后续一切报告注记 **"不可归因旧口径差额 −12"**,不得写成 5,225 已复现;正式样本 4,892(可判 5,175)以冻结规则实现为唯一权威 | 验收档 §11 + STATE 落档;零代码改动 |
| ② | driver 第 96 行注释口径 | `reference_reconciliation` docstring 参考层锚定改为与实现一致:候选 12,569 ↔ **全期候选+时序违例恒等锚**(`candidate_allperiod_plus_temporal = candidate_rows_all_periods + temporal_violation`);**只改说明,计算零触碰** | `git diff 4eb404d..00cf8c1` 该文件仅 docstring 两行;exp20 三件 fixture 两台 33/73/19 全绿 |
| ③ | R6 第三处硬编码 | 第 340 行 `r6_ledger_after == r6_ledger_before == 25` → `r6_ledger_after == r6_ledger_before`(前后相等,不绑字面行数);第 354 行文案→"状态及结果槽前后不变、且状态非registered" | **pap_gate aliyun 带 DSN 重跑 23/23 PASS**;证据③实测输出=`台账行数25→25 exp8(状态及结果槽前后不变、且状态非registered)('done',False,False)→('done',False,False)` |

## 2. 版本纪律

- **行为代码基线止于 `4eb404d`**;本单元 commit 链=`ad9870c`(人令留痕)→`00cf8c1`(窄修施工)→本回执 commit(验收档 §11+STATE+本档),**全部为文档/测试面,零生产逻辑**。
- 当前 HEAD=本回执 commit(git log 首行;两台同 HEAD、git 净,实测见 STATE)。

## 3. 禁区与实物核对(2026-07-19 查库实测)

- 禁区维持:**零收益读取/零 manifest/零正式运行/零 persist**。
- exp20 仍 frozen,pap_json MD5 `a7cdd235240a6632b014913b5472c94d` 未变,result/done 槽空;台账 25 行=registered 16/frozen 3/done 5/closed 1 未动。
- 下一步(须人令)=外部复核闭合后另令授权 manifest+§7 单次正式运行。
