# exp13 `limit_down_open` PAP 草案 · 状态标记档(2026-07-21 晚)

> 依据 = 人终版收口令 2026-07-21 五.2(留痕 `taosha/docs/limit-down-open-pap-final-order-2026-07-21.md`)。
> 草案 JSON 本体是 canonical 字节本体(文件 SHA==digest),故状态标记以本档承载,草案文件零改动。

- 草案实物 = `taosha/docs/limit-down-open-pap-draft-2026-07-21.json`,
  文件 SHA256 == canonical digest == `a432877a0953c50b2bb3c1064faa19fc611f1cbeb1cfbd45a76ce1231a6189e2`。
- **状态 = `NOT-FROZEN`(继续保留):该 digest 从未冻结**——未写入数据库、未入冻结记录、
  未入正式运行参数,此后也不再进入冻结流程。
- **已被终版候选取代(但从未冻结)**:终版候选 =
  `taosha/docs/limit-down-open-pap-final-2026-07-21.json`,
  文件 SHA256 == canonical digest == `583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42`;
  草案→终版差异 = 仅终版收口令二.2(N_MIN=2 精确化)+二.3(snapshot 身份精确化)两键三处文本,
  逆向三替换逐字节还原草案(证明见交付档 §9.2)。
- 任何预判、冻结句均不得绑定草案 digest `a432877a…89e2`;终版候选 digest 的冻结与预判绑定
  须由人另下令(终版收口令四/六)。
