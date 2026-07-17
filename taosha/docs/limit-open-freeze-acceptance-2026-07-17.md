# exp8 limit_open · PAP v3 冻结执行验收档(2026-07-17 深夜五令,实际提交时刻 2026-07-18 00:26 CST)

> 令原文档:`taosha/docs/limit-open-freeze-order-2026-07-17.md`(原文即口径,留痕 commit `9a52f08`)。
> 绑定 digest:`afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb`(下称 `afd8443a…addb`)。
> 新预判密封句(人裁,针对本 digest):**主窗市场调整后 CAR 为负,把握度 60%**;原"负向/55%"维持作废,不平移不并存。

## §1 前置六项只读基线(冻结前实测,全 PASS)

| # | 令项 | 实测 | 判 |
|---|------|------|----|
| 1 | status=registered,frozen_at/done_at 空 | `8\|registered\|NULL\|NULL`(exp8=limit_open trial 1「连续一字涨停开板」) | PASS |
| 2 | result_json 为空 | `result_json IS NULL = true` | PASS |
| 3 | 不存在 exp8 正式研究 manifest | `study_snapshot` 全 6 行(1/2/38/40/74/87)逐行核:全系硬化验收件/exp4 链,content/note 对 `limit_open`/`exp8` 检索零命中 | PASS |
| 4 | 不存在 exp8 正式运行/产物登记 | `experiment_addendum` exp_id=8 计 0;result 空;aliyun `/root` 无任何 limit_open/s8 运行目录 | PASS |
| 5 | 工地端文件 SHA256 与引擎重算均等于 digest | **两台**(AWS+aliyun,同 commit 树)实测:文件 SHA256 = `canonical_pap_sha256()` 重算 = `afd8443a…addb` 三值全等 | PASS |
| 6 | 台账行数/分布不因冻结新增行 | 冻结前 25 行 = registered 18 / frozen 2 / done 4 / closed 1 | PASS(基线) |

## §2 冻结执行(既有状态机,单事务)

- 执行身份 = `taosha_app`(`ledger.connect()`,psycopg 非 autocommit);脚本留档 aliyun `/root/s8freeze/freeze_exp8.py`(600),日志 `/root/s8freeze/freeze_exp8.log`。
- 事务序(一次 COMMIT):
  1. `SELECT … FOR UPDATE` 行锁内前置断言(registered/三槽空/台账 25 行);
  2. `UPDATE pap_json = PAP v3 原文`(载荷=仓内 `limit-open-pap-final-v3-2026-07-17.json` 逐字节读入解析,无改写/无旧版复制/无运行时补键;011 触发器:pap_json 仅 registered 态可改——合法窗口);
  3. `ledger.freeze(8)`(既有状态机 registered→frozen,置 frozen_at;经库侧 `_pap_freeze_gate`:exp8 ∈ pap_legacy_registry,v3 带 `pap_schema_version=2`+`analysis_type='event'`,legacy 升级路径=仅事件版,放行);
  4. COMMIT @ **2026-07-18 00:26:26.780743+08**。
- 注:令签发于 07-17 深夜,实际执行时刻已过京时零点(07-18 00:26),如实记,不改档名。

## §3 冻结读回验收(令二逐项,全 PASS)

| 令项 | 读回值 | 判 |
|------|--------|----|
| status | `frozen` | PASS |
| frozen_at | `2026-07-18 00:26:26.780743+08` | PASS |
| DB pap_json canonical SHA256 | `afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb` == 令绑定 digest | PASS |
| pap_json 载荷 MD5(补充对账) | `md5(pap_json::text)` = `ec74f93f678598016dcf5dbd4721b94f`(taosha_app 读回与 postgres 独立连接双侧同值) | PASS |
| DB 读回 vs 仓内 v3 结构化全等 | Python `parsed_equal = True`(DB jsonb 解析对象 == 文件解析对象) | PASS |
| 台账总行数不变 | 25 行(分布迁移为 registered 17 / **frozen 3** / done 4 / closed 1,exp8 一行迁态,零新增零删除) | PASS |
| 冻结留痕 commit / 两台同步 / 工作区 | 本档所在 commit(见 git log);push origin + aliyun `git pull --ff-only`,两台 `git status` 净 | PASS(commit 后即验) |

- 独立复核:postgres 超级用户连接读回 status/frozen_at/md5/result_json 空,与 taosha_app 读回全等。
- result_json 仍为空、done_at 仍为空——persist 边界(令四)未触碰。

## §4 冻结后即时状态

- exp8 = frozen,pap_json 自此触发器焊死(铁律④:冻结后不可改,改参=INSERT 新行)。
- 授权链下一步 = driver 最小施工(逐字消费 PAP v3 `engine_params`,传 `pap_sha256_assert=afd8443a…addb`,不一致 fail-closed,不改默认路径与其他实验输出)→ driver 专项验收 → manifest 生成发布 → §7 单次正式运行 → 运行产物取证。
- persist 不在授权内:§7 后 exp8 保持 frozen、result 槽空,待人验收另令。
