# exp8 limit_open · PAP v3 冻结令(人裁原文,2026-07-17 深夜五)

> 收令渠道:施工会话人令原文。**原文措辞即口径,不得善意改写。**
> 绑定对象:`taosha/docs/limit-open-pap-final-v3-2026-07-17.json`
> digest = `afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb`

## 人令原文(逐字)

批准冻结 exp8 PAP v3,绑定 digest:
afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb
新预判:主窗市场调整后 CAR 为负,把握度 60%。
本预判是针对上述 PAP v3 digest 的新裁定,不继承此前已作废的旧预判或未冻结版本;原"负向/55%"预判继续维持作废状态,不得平移或并存。

一、冻结执行前置
先只读回报 exp8 基线:
status=registered,且 frozen_at、done_at 均为空;
result_json 为空;
不存在 exp8 正式研究 manifest;
不存在 exp8 正式运行或运行产物登记;
工地端 PAP v3 文件 SHA256 与引擎 canonical_pap_sha256() 重算值均等于上述 digest;
台账总行数及各状态分布,不得因冻结新增实验行。
任一不符立即停止并上报,不得自行修正状态。

二、冻结执行
前置全部通过后,方可按既有状态机执行 registered → frozen,冻结载荷必须是 PAP v3 原文,不得人工改写、复制旧版或运行时补键。
冻结后直接读回并提交:
status、frozen_at;
数据库 pap_json 的 canonical SHA256,必须等于
afd8443a50d611e950bf7987b5689f86a477e65dfb19847b28344b7f1768addb;
pap_json 载荷 MD5,作为补充对账项;
DB 读回 PAP 与仓内 v3 PAP 的结构化全等证明;
台账总行数不变;
冻结留痕 commit SHA 及两台同步、工作区状态。

三、冻结后授权范围
冻结验收通过后,授权依次执行:
driver 最小施工 → driver 专项验收 → manifest 生成发布 → §7 单次正式运行 → 运行产物取证
driver 必须:
逐字消费 PAP v3 的 engine_params,不得保留运行时自由选择;
向引擎传入 pap_sha256_assert=afd8443a…addb;
对参数或 digest 不一致一律 fail-closed;
不改变既有默认路径和其他实验输出。
各节点任一失败立即停止,不得跳步或旁路。

四、persist 边界
本令不授权 persist。
§7 运行结束后,保持 exp8 为运行前既有可验收状态,台账结果槽不得写入;先提交原始 result、report、run log、SHA256 清单、manifest 读回及只读台账基线,待人完成结果验收后另行下达 persist 令。

## 工地注记(非口径,仅执行索引)

- 本令为 07-17 深夜四停交验点(等人重审 PAP v3)的解锁令;PAP v2(`2611be36…`)维持 NOT-FROZEN,旧预判"负向/55%"维持作废。
- 冻结载荷合法路径 = registered 态单事务 `UPDATE pap_json = PAP v3 原文` + 既有状态机 `ledger.freeze(8)`(011 触发器:pap_json 仅 registered 态可改;registered→frozen 过 `_pap_freeze_gate`)。
- persist 不在本令内;§7 后 exp8 台账行保持 frozen 态、result 槽空。
