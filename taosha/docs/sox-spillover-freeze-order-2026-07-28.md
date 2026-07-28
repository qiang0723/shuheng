# exp24 sox_spillover PAP v2 冻结+最小适配授权 · 人令留痕（2026-07-28，UTC+8）

> 发令人：老板；收令渠道：本项目工作会话。人的预判原文与授权确认不得改述。

## 一、人的预判原文

> 同向，把握度60%

冻结口径映射（PAP已定义）：`同向`对应主窗`[0,+4]`市场调整后`signed CAR`为正；
只押方向，不押幅度，不预判统计显著性。预判仅绑定本令PAP v2 digest，不继承旧版本。

## 二、经人认可的冻结授权原文

架构窗口提交如下授权句后，人回复“认可”：

> 批准冻结exp24 PAP v2，digest=`be26a7f43e1dca2602a4ab60931aae4db9e55781cbf1cba410dc2d4d0f738f27`。预判原文：“同向，把握度60%。”同向对应主窗市场调整后signed CAR为正，仅押方向，不押幅度或显著性。冻结前确认exp24仍为registered三槽空、无研究manifest、台账13/2/9/1、PAP文件SHA与canonical一致；符合后走既有状态机单事务冻结，冻结后应为12/3/9/1。随后授权最小适配与fixture，停在行为验收点；暂不授权研究manifest、正式运行或persist。

## 三、执行边界

- 冻结载荷唯一来源：`taosha/docs/sox-spillover-pap-final-v2-2026-07-28.json`；
- 生产写入仅限既有exp24行的PAP载荷更新与`registered→frozen`状态迁移，同连接单事务；
- 冻结后只授权exp24规则、driver、报告与攻击fixture的最小适配及只读漏斗复现；
- 不授权exp24研究manifest、A股正式收益研究、正式运行、result persist或其他台账写入；
- 行为验收完成即停交验点。
