# exp12 `st_removal` PAP 草案 · 状态标记档(2026-07-23)

> 依据 = 人终版收口令 2026-07-23(留痕 `taosha/docs/st-removal-pap-final-order-2026-07-23.md`,
> F 条 commit `3564a23` 先行)。草案 JSON 本体是 canonical 字节本体(文件 SHA==digest),
> 故状态标记以本档承载,**草案文件零改动**。

- 草案实物 = `taosha/docs/st-removal-pap-draft-2026-07-23.json`,
  文件 SHA256 == canonical digest == `12e8366de0c60ca33065e1a53ac10cd3d92cbd8214c23f2498266ab5ab4dcf41`。
- **状态 = `NOT-FROZEN`(继续保留):该 digest 从未冻结**——未写入数据库、未入冻结记录、
  未入正式运行参数,此后也不再进入冻结流程。
- **已被终版候选取代(但从未冻结)**:终版候选 =
  `taosha/docs/st-removal-pap-final-2026-07-23.json`,
  文件 SHA256 == 引擎 canonical 重算 digest ==
  `62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353`;
  草案→终版差异 = 恰 7 键、令内 11 处替换(τ0 唯一口径/postpone_policy='missing_bar_only'/
  cost 角色/一字板 NFV 执行限制/641 对账参考身份/沿承键批准落记),
  **逆向 7 键还原逐字节 == 草案文件**(证明见交付档 §3.3)。
- 草案 `cleaning` 键内 unified 与『有 bar 即可交易』两读并列文字,经终版令择一后于终版删除;
  S2-DEC3 unified 口径对本假设作废,不得并存(改判纪律:作废记录在此与 STATE,不入终版 PAP 正文)。
- 任何预判、冻结句均不得绑定草案 digest `12e8366d…dcf41`;终版候选 digest 的冻结与
  方向+把握度预判绑定须由人另下冻结令(人亲拟)。
