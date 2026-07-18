# exp20 earnings_revision · PAP v2 冻结执行验收档(2026-07-18 深夜六令,实际提交时刻 2026-07-19 00:26 CST)

> 令原文档:`taosha/docs/earnings-revision-freeze-order-2026-07-18.md`(原文即口径,留痕 commit `89396cc`)。
> 绑定 digest:`e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`(下称 `e1d18dc1…7fd5`)。
> 预判密封句(人裁,只绑本 digest,仅方向直觉不预判显著性):**主窗市场调整后 signed CAR 为负(下修后反弹、上修后回吐),把握度 55%**;旧版本表述(含 94b9ba78 相关)不继承不平移。

## §1 冻结前六项只读断言(令一,执行写入前实测,全 PASS)

| # | 令项 | 实测 | 判 |
|---|------|------|----|
| 1 | exp20 status=registered | `20\|earnings_revision\|1\|业绩预告修正公告\|llm\|prescreen\|registered` | PASS |
| 2 | result_json/frozen_at/done_at 均空 | 三槽全 NULL | PASS |
| 3 | 无 exp20 研究 manifest 或正式运行记录 | `study_snapshot` 全 7 行(1/2/38/40/74/87/121)逐行=硬化/exp4/exp8 链;content+note 对 `exp20`/`earnings_revision` 检索零命中;`experiment_addendum` exp_id=20 计 0;aliyun `/root` 无 s20/earnings/forecast 运行目录 | PASS |
| 4 | 台账总行数 25 | 25 行 = registered 17 / frozen 2 / done 5 / closed 1(冻结前基线) | PASS |
| 5 | v2 文件 SHA==引擎 canonical 重算==令 digest | **两台**(AWS+aliyun,同 commit 树)实测三值全等 `e1d18dc1…7fd5`;validate_pap PASS;parse_test_windows=(5,20,60) | PASS |
| 6 | 库内当前登记 PAP=未冻结占位载荷 | 10 键,`window/cleaning/benchmark/cost/pool.universe/snapshot_batch_req` 均为"待冻结…"字样占位,无 pap_schema_version | PASS |

## §2 冻结执行(令二,既有状态机,单事务)

- 执行身份 = `taosha_app`(`ledger.connect()`,psycopg 非 autocommit);解释器 `/opt/venvs/qbase-ingest/bin/python3`(psycopg 3.3.4);脚本留档 aliyun `/root/s20freeze/freeze_exp20.py`(600),日志 `/root/s20freeze/freeze_exp20.log`。
- 事务序(一次 COMMIT):
  1. `SELECT … FOR UPDATE` 行锁内前置断言(registered/三槽空/台账 25 行)——全 PASS;
  2. `UPDATE pap_json = PAP v2 原文`(载荷=仓内 `earnings-revision-pap-final-v2-2026-07-18.json` 逐字节读入解析,无改写/无运行时补键;011 触发器 registered 态合法窗口);
  3. `ledger.freeze(20)`(既有状态机 registered→frozen,置 frozen_at;库侧 `_pap_freeze_gate`:exp20 ∈ pap_legacy_registry(实测 t),v2 带 `pap_schema_version=2`+`analysis_type='event'`,legacy 事件版路径放行);
  4. COMMIT @ **2026-07-19 00:26:27.189927+08**。
- 注:令签发于 07-18 深夜,实际执行时刻已过京时零点(07-19 00:26),如实记,不改档名(同 exp8 先例)。
- 首跑因 root 系统 python 无 psycopg 在 `import` 处即失败(任何连接建立前),零 DB 写入,exp20 读回仍 registered 后换解释器重跑,如实记。

## §3 冻结读回验收(令二逐项,全 PASS)

| 令项 | 读回值 | 判 |
|------|--------|----|
| status | `frozen` | PASS |
| frozen_at | `2026-07-19 00:26:27.189927+08` | PASS |
| 文件 SHA256 | `e1d18dc1…7fd5` | PASS |
| 引擎 canonical digest(文件侧重算) | `e1d18dc1…7fd5` | PASS |
| DB 载荷 canonical digest(库读回重算) | `e1d18dc1…7fd5` == 令 digest | PASS |
| parsed_equal(DB jsonb 对象==文件解析对象) | `True` | PASS |
| 载荷 MD5(`md5(pap_json::text)`) | `a7cdd235240a6632b014913b5472c94d`(taosha_app 读回与 postgres 独立连接双侧同值) | PASS |
| 台账只迁 exp20 行不新增 | 25 行,分布 **registered 16 / frozen 3 / done 5 / closed 1** = 令预期 16/3/5/1,零新增零删除 | PASS |
| result_json/done_at 仍空 | 双 NULL(persist 边界未触碰) | PASS |

- 独立复核:postgres 超级用户连接读回 status/frozen_at/md5/schema_version=2/analysis_type=event,与 taosha_app 读回全等。
- 冻结不可改探针:taosha_app 对 pap_json 真实改动(附加键)→ 触发器 RAISE `铁律④违反: pap_json 冻结后/离开 registered 态不可改`(事务 ROLLBACK,零残留,MD5 复核未变);同值 no-op UPDATE 放行属触发器语义(仅拦真实改动),无害。

## §4 冻结后即时状态与本单元边界

- exp20 = frozen,pap_json 自此触发器焊死(铁律④:改参=INSERT 新行)。
- 本单元授权(令三,分段授权只到行为验收):forecast 只读视图对+事件生成器最小适配 / signed 统计路径+公告事件顺延+direction 诊断轴参数化 / 14 组预注册攻击 fixture / 12,569·5,225 参考数逐层对账(对不上不得改冻结规则,异常即停报人)/ 全家福回归+既有默认路径零回归;特别验证七项见令原文。
- **本单元仍禁止**:正式读取或计算真实收益结果;生成正式研究 manifest;正式运行事件研究;persist 或写入 result_json。
- 代码与 fixture 验收后停交验点;通过外部只读复核后,另行授权 manifest 与单次正式运行。
