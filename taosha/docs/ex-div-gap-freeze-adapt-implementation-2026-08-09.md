# exp14 `ex_div_gap` · 冻结回执与最小适配实现点

- 日期：2026-08-09（UTC+8 / Asia/Shanghai）
- 授权令：`taosha/docs/ex-div-gap-freeze-adapt-order-2026-08-09.md`
- 终版 PAP digest：`a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`
- 密封原文：`正，把握度60%`

## 一、冻结事务

冻结前只读硬闸确认 exp14=`ex_div_gap/trial1/llm/prescreen/registered`，三槽空、addendum=0；
PAP 文件 SHA、canonical 重算与授权 digest 三者一致；source snapshot375 在 taosha 权威行、qbase
镜像与 publication attestation 三处 digest 均为 `2df8e289…a6b7`，13 键 qbase 向量中实际
消费 `dividend=17/adj_factor=7/trade_cal=10`；台账26=`registered7/frozen2/done15/closed2`。

2026-08-09 14:33:15.200827+08（UTC+8）以同一 `taosha_app` 连接执行单事务：

1. `FOR UPDATE` 重做全部前置断言；
2. 写入终版 PAP canonical 原文；
3. 调用既有 `ledger.freeze(14)`；
4. 一次 COMMIT。

后核验为 `frozen`、`result_json/done_at` 仍空、PAP parsed equality=true、canonical 命中、
载荷 MD5=`46ecfcac84fd79e904731b05ca4ba115`，台账26=`6/3/15/2`，StudySnapshot仍20行
max=398。冻结后真实改参探针被铁律④拒绝，回滚前后 MD5 相同。

冻结前 source375 current/snap 选择再次精确复现 `4,035`、恰等 `1,083`、selection SHA
`ef9529b12305be0d618bac62020a264eba03c2ec46ec0f54505ee5b47b977f2f`；仅为 NFV 同锚参考。

## 二、失败痕迹与零残留

- recon attempt1：取证目录属主不匹配，已完成只读计算但写 JSON 被拒；零数据库写；
- freeze preflight attempt2：取证脚本以 tuple 方式读取 `dict_row`，在任何写入前停止；直读确认
  exp14 与台账未变，修正仅限取证脚本行访问；
- 八组映射 attempt1/2：容器先后因工作树与 `PYTHONPATH` 未指向只读挂载树，在数据库连接前停止；
- 八组映射 attempt3：旧分类近似误用了严格组件校验，完成只读分类后因交叉矩阵断言不符停止；
  纠正为窄闸六字段原始 Decimal 精确比较，未改事件规则或数据库。

失败脚本/日志均保存在 `aliyun-new:/root/s14freeze/`，未删除、未覆盖成功件。

## 三、八个多行组交叉表

| 窄闸分类 | 严格 B1 分类 | 组数 |
|---|---|---:|
| conflict | component_invalid | 2 |
| conflict | multi_null | 1 |
| foldable | component_invalid | 1 |
| foldable | multi_null | 4 |

逐组明细共8组，恒等式 `2+1+1+4=8`；窄闸侧 `foldable=5/conflict=3`，严格 B1 侧
`component_invalid=3/multi_null=5`。明细与精确断言在 `multirow_mapping.json`，全部 NFV。

## 四、最小适配触碰面

- `taosha/harness/run_ex_div_gap_recon.py`：在原 recon 入口内收编冻结 PAP/digest、8键参数、
  source375 防冒充、同日 `tau0_on_anchor` 文本硬门、正式模式骨架与身份水印；recon 与正式选择
  共用同一规则路径；
- `taosha/engine/report_ex_div_gap.py`：专属小型报告片段，缺真快照、身份水印、结构化因子/raw
  机械审计或执行限制审计均 fail-closed；
- `taosha/engine/report.py`：只增加 exp14 显式路由，文件与 `render` 行数均不高于既有棘轮；
- `taosha/compute/ex_div_gap_rules.py`：只新增事件资格已确定后的 adj_factor 比例 NFV 汇总，
  selection SHA 的事件投影不变；
- `taosha/harness/verify_ex_div_gap_adapter.py`：覆盖 digest、8键缺多、同日τ0文本攻击、signed旁路、
  source375冒充、身份删除、执行审计删除、结构化NFV术语与唯一递归 verdict。

统计内核 `runner.py`、清洗内核 `cleaning.py`、通用 reader/数据库 DDL 均零改动；未生成研究
manifest，未进行正式收益读取或 §7 运行。

## 五、本地验证与当前停止点

- `verify_ex_div_gap_rules`：14/14 PASS；
- `verify_ex_div_gap_adapter`：38/38 PASS；
- 既有31项离线 rules/adapter/engine/冻结不可变/三窗口/敏感性套件：全绿；
- `verify_code_size`：PASS，223文件/33,242行/922函数，债务仍20文件/50函数；新增/修改的
  exp14 文件均≤300行、函数≤60行，`report.py`/`render` 未突破既有654/481棘轮；
- `git diff --check`：PASS。

当前仅完成本地适配实现与冻结取证；须将本实现 commit 推送后，阿里云以 source375 运行冻结态
recon、数据库硬门与镜像内回归，再生成最终行为验收档。此前不进入研究 manifest、正式收益、
§7、result 或 persist。
