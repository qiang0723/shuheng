# exp24 PAP v1 终版候选状态标记

`sox-spillover-pap-final-2026-07-28.json` 从未冻结，文件 SHA256及canonical digest为
`702637cb21ae2a6fb50b48a54574aac9a0e57c596bca6f8a1b90bc0db58e675a`。

外部只读复核发现既有数据质量披露漏项：批13早期388行`currency`为空字符串，以及
2015-02-02主锚与Yahoo的单日差异未写入PAP数据质量声明。v1本体保持历史原样，已由
`sox-spillover-pap-final-v2-2026-07-28.json`取代；不得冻结、生成研究manifest或运行。
