# exp568（旧exp15）`st_imposition` · PAP冻结回执（2026-07-29）

## 结论

exp568已通过既有状态机由`registered→frozen`，一次COMMIT成功；`frozen_at=2026-07-29 19:23:34.970260+08`。

冻结PAP digest=`56fffa4a221afd48b40b65e65f4799beffdbba64b90abfff6f1c9e592b2c5b58`。数据库载荷与终版文件`parsed_equal=True`，引擎canonical重算同值，库载荷MD5=`cb7fbc6dad74fad0432376e2df9f4497`。

## 前置与后核验

- 冻结前：exp568=`delist_warning_financial/trial 2/registered`、四槽空、零manifest；终版文件SHA=canonical=令digest；数据库登记载荷13键；台账26=`11/2/11/2`；
- 冻结后：exp568=`frozen`、`result_json/done_at`仍空；台账26=`registered 10 / frozen 3 / done 11 / closed 2`，恰迁一行零新增；
- 旧exp15保持closed，exp22保持trial 1 registered；
- 人的预判原文“负，把握度60%”已在冻结令先行留痕，仅押主窗方向、绑定本digest。

## 证据与边界

证据目录=`/root/s568freeze/`，脚本与日志`sha256sum -c`全过；`SHA256SUMS`文件SHA=`fb891eb93407d8958fb102957980695b304661b1fe3674c6f6acb554272e2b48`。

本步骤零manifest、零收益读取、零正式运行、零persist。下一步仅按同一令进入最小适配，停行为验收点。
