# exp16 `yearend_strength` · 冻结与最小适配行为验收（2026-07-30）

## 1. 二元结论

**行为验收通过，停在行为验收点。** exp16 仍为 frozen，结果槽空；本单元没有生成正式研究
manifest、没有执行 §7、没有 persist。

冻结凭证见 `yearend-strength-freeze-receipt-2026-07-30.md`。施工链为：

1. `58e3bc5`：人令留痕，F 条先行；
2. `8d6c383`：exp16 专属规则、driver、报告模块与两套 fixture；
3. `867afab`：recon 显式钉定 `market_return=88`；
4. `ebd8881`：recon 的直接市场批连接强制只读；
5. `e7b79e9`：重复事件键整组全剔，并补攻击 fixture。

## 2. 触碰面与结构

生产触碰仅为 exp16 专属新增件及 `report.py` 显式分支：

- `taosha/compute/yearend_strength_rules.py`：148 行，纯规则、无 I/O；
- `taosha/harness/run_yearend_strength_study.py`：286 行，函数均不超过 49 行；
- `taosha/engine/report_yearend_strength.py`：52 行；
- `taosha/engine/report.py`：只增 exp16 显式标题与选择审计分支；
- 两套 fixture：rules 119 行、adapter 173 行。

未修改统计内核、清洗内核、PAP schema、qbase DDL 或既有实验规则。exp16 使用自己的 8 键
`engine_params` 恰等白名单并逐字消费，`st_policy=keep` 来自冻结 PAP；`tau0_on_anchor=True` 只在逐字
核验冻结文本后启用，不是运行时自由参数。

## 3. 规则与攻击面

规则以 Decimal 精确实现：选择年 2010..2023，每年 12 月最后 10 个 SSE 开市日加前一基期日组成
严格 11-bar 面板；相对财富
`exp(ln(close_d10/close_d0)-sum(market_log_return_d1..d10))-1 >= 0.05`；事件日为次年首个
SSE 开市日。缺 bar、非正价格、市场收益缺失、输入乱序、原始重复或重复事件键均 fail-closed；重复
事件键涉事组全剔，不择一。

最终专项 fixture：

- `verify_yearend_strength_rules.py`：`14/14 PASS`；
- `verify_yearend_strength_adapter.py`：`25/25 PASS`。

覆盖恰 5%、略低拒绝、11-bar 边界、缺基期/窗内 bar、禁止按个股行序补足、市场收益缺失、异常价格、
原始重复、重复事件整组全剔、输入乱序、14 个年度窗、digest 与 8 键缺/多键、snapshot/manifest 路由、
τ0 当日、ST keep、缺 bar 顺延 5/6 日及报告术语与唯一 verdict。

## 4. recon 对账

recon 使用 source snapshot 74 的 qbase 钉批视图，并显式只读消费 `market_return=88`。正式模式仍只
接受未来 exp16 自有研究 manifest，拒绝 snapshot 74 冒充。

最终 HEAD 上双跑结果逐字相同：

- 两件 JSON SHA256 均为
  `0dbaddab9da08b48dcf60ec35128fc19963b1fa1f5a7ae20b7aeb35b0d3959fa`；
- 年度面板 `46,290 = 完整 44,417 + 缺 bar/不完整 1,873`；
- 基期缺失 641，窗内缺失 1,744，非正价格 0；
- 事件 `7,751`，证券 3,727，事件日 14；事件锚有 bar 7,728、缺 bar 23；
- 重复事件组与剔除行均为 0；
- selection SHA256=
  `057f5252183cd61cef4c52b2fd663e00eaed44ac5efe1825f7a9ecd8040355c7`；
- 面板、年度分布、事件锚三条恒等式均为 true，参考对账 exact_match=true。

施工中两次 recon 启动均在产出前被既有数据库硬门拒绝：先是 source snapshot 74 不含 taosha
`market_return` 键，后是只读 engine 角色无底表权限。随后把 recon 路由明确为 snapshot 74 + batch 88，
并以 app 连接读取该批但会话首句强制 `default_transaction_read_only=on`；正式路径保持 engine 身份和
manifest 路由不变。两次均零结果、零研究写入、零台账动作，不是正式运行或重跑。

## 5. 回归与环境痕迹

阿里云专项、既有离线全家福全部通过；数据库套件：状态机 `46/46`、PAP 硬门 `23/23`、addendum
`14/14`、镜像 `11/11`、血缘 `24/24`、StudySnapshot probes `19/19`、集成 `7/7`。既有离线各实验
fixture 全绿，三窗与冻结不可变检查通过。合成 e2e 双跑均等于历史基线
`3116ba9b74f7c53b94082c93a476df2257d7a28eae2ad1faa0665b63716a4c22`。

本地 macOS 系统 Python 3.9.6 不支持仓内 `dataclass(slots=True)`，首次本地 adapter 启动在导入阶段
退出；正式本地验证改用钉定 Docker Python 3.14 环境，镜像 ID=
`sha256:7c9a0ea141adea31cbdebc22f0b9923f0e6a69923d0bebf7057a979587b2acd9`。另一次
StudySnapshot 套件调用漏传必需的 `--mode`，CLI 在连接前拒绝；按正式参数 `--mode probes` 复跑
`19/19 PASS`。以上均为测试编排痕迹，未改变研究实物。

阿里云证据目录 `/root/s16adapt/` 的 `SHA256SUMS` 排除自身及校验日志后共 47 件，`sha256sum -c`
全通过。

## 6. 停止线

只读终态：exp16=`frozen`，`frozen_at=2026-07-30 11:01:09.498726+08`，`result_json/done_at`
为空；台账 26 行=`registered 9 / frozen 3 / done 12 / closed 2`。无 exp16 正式 manifest。

下一步仅可在外部行为复核通过后，由 John 另行授权 exp16 自有研究 manifest 与 §7 单次正式运行；
persist 仍须结果验收后单独授权。

