# r3disc 判别力并发补测证据归档(2026-07-13 产出,2026-07-15 归档)

按 2026-07-15 排产令 §1(`docs/holder-sell-scheduling-order-2026-07-15.md`)行政闭卷归档。
源 = 阿里云 `/root/r3disc/`(隔离环境补测产物;归档核验通过后按令整体删除,本目录为唯一存放)。

## 文件对照

| 文件 | 说明 |
|---|---|
| `evidence.json` | v1 判别力补测证据(RUN1/RUN2,水印批 11/12;后被时序判点退回,留档) |
| `evidence2.json` | **v2 时序修正证据(RUN3/RUN4,水印批 13/14;四时点严格不等式,终结论采信)** |
| `orchestrate.py` / `orchestrate.log` / `orchestrate_stdout.log` | v1 编排脚本+日志 |
| `orchestrate2.py` / `orchestrate2.log` / `orchestrate2_stdout.log` | v2 编排脚本+日志 |
| `mret_seed.log` / `pret_seed.log` | v1 两 seed(market_return / pool_b1_return)时间戳日志 |
| `mret_seed2.log` / `pret_seed2.log` | v2 两 seed 时间戳日志(四份时间戳日志=本 4 件) |
| `SHA256SUMS` | 逐文件 SHA256 清单(源机计算,本机复算全等) |

注:`orchestrate_stdout.log`==`orchestrate.log`、`orchestrate2_stdout.log`==`orchestrate2.log`(sha 逐字节同,tee 双写产物),照实归档不去重。

## 关联验收档(已在仓,git 历史即不可变载体)

- `taosha/docs/postaudit-round3-narrow-acceptance-2026-07-13.md`(§10/§11/§12 全案)
  sha256 = `25f5d5455b9245d1394f5bb198fb38fdb7cc5044c6d243ebf481cf13d3f9a253`(归档时点实测)

## 核验记录

- 秘密扫描(password/secret/token/api_key/私钥块/AKIA/sk-/DSN 带密码/PGPASSWORD 全模式):**零命中**(2026-07-15,源机 /root/r3disc 执行)。
- 异机读回:阿里云原件 sha256 ↔ AWS 拉取件 sha256 **12/12 全等**(2026-07-15)。
- push 后阿里云 `git pull` 复算见行政闭卷档 `docs/hardening-window-closure-2026-07-15.md`。

## 证据链代码锚

- v2 跑批代码基 = 隔离树 HEAD `8b538e4`(evidence2.json 内 code_head 字段自证;8b538e4→2b4e743 仅 docs/STATE 差异,seed 代码零差异)。
- 隔离 git 树 `/root/r3disc/quant` 按令不保留(与 GitHub 仓同源,commit 可随时检出)。
