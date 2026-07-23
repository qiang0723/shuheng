# exp12 `st_removal` 行为验收通过 + manifest 与 §7 单次正式运行授权令(原文留痕,2026-07-23)

> 人令下达于会话内(2026-07-23 二深夜),本档为 F 条裁决留痕,**原文措辞即口径,不得善意改写**。
> 令性质:行为验收通过确认(含两项裁定)+授权 exp12 自有研究 manifest 生成发布+§7 单次正式
> 运行。**不授权代码修改、重跑或 persist;完成后停取证点。**

## 人令附注(验收往来,逐字要点)

- 两项裁定:①`st_policy='keep'` 批准——"它是完整摘帽事件定义的必然实现,不是新的可选参数;
  必须固定在driver和result audit中,不得开放运行时选择,也不新增ST分层";②状态不可判新增
  2 例批准——"两例均fail-closed排除、最终641事件不变,属于更保守的识别,不需要改规则"。
- 人本机复跑注记:规则 fixture 本机 42/42 PASS;adapter 因本机 Python 3.9 不支持项目
  `dataclass(slots=True)` 未能启动——**本地运行时限制,非测试断言失败,服务器 43/43 凭证
  维持有效**(留痕如实记录)。

---

## 人令原文

**枢衡工地:**

exp12冻结与最小适配行为验收通过。

确认:

1. `st_policy='keep'`为冻结事件定义的必然实现,固定消费、不得成为运行时选择;实际值写入result audit,不设ST收益分层。
2. 状态不可判新增2例按现有fail-closed处置,逐条留痕,最终事件集不受影响。

现授权:

- 生成并发布exp12自有研究manifest;生成前读回source snapshot及namechange批次,须与事件数据实际来源一致;
- 完成权威行、qbase镜像和publication attestation三处发布,digest必须一致;
- 仅执行一次§7正式运行,PAP digest固定为`62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`;
- 若数据向量变化、事件集差异无法按血缘解释、RC非零或锚定断言失败,立即停止,不自动重跑;
- 运行后保持exp12为frozen、result_json与done_at为空、台账零写入;
- 留存result/report/log原件及SHA256,传输前秘密扫描,交验后另行决定persist;

本令不授权代码修改、重跑或persist。完成后停在取证点。

---

## 执行序(照令,承 exp13/exp20 §7 先例)

①前置只读读回(source snapshot 三处 digest+namechange 批次==事件源实际批次+exp12 frozen/
PAP canonical==令 digest+台账 25=14/3/7/1)→ ②manifest 生成发布三步(权威行/qbase 镜像/
publication attestation,三处 digest 全等;血缘+镜像核验)→ ③§7 单次正式运行(digest 断言;
事件集 641 血缘对账;停止条件=向量变化/事件集差异无法血缘解释/RC≠0/锚定断言失败,立即停
不自动重跑)→ ④运行后核验(exp12 仍 frozen/result·done 空/台账零写入)→ ⑤取证(原件+SHA256+
秘扫)→ 停取证点。
