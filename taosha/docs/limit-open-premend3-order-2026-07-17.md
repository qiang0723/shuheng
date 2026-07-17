# exp8 回修三令(人转外部复核结论,2026-07-17 深夜四)· 裁决留痕(F 条,原文即口径)

> 本档为人转达的外部复核结论**逐字留痕**。效力:回修二主体通过;PAP v2(digest
> `2611be36a37b89055a5e4c393f18c507492b36fa51db323db66d43be370b66b4`)**暂不批准冻结**,
> 只退回以下两个窄阻塞,不扩大范围。修正后另建 PAP v3;v2 保留并标记
> "外部复核未通过、未冻结",不得覆盖修改。

## 人令原文

外部复核结论:回修二主体通过,但PAP v2暂不批准冻结。只退回以下两个窄阻塞,不扩大范围。

一、P1-4的"来源锚"目前不是真锚

当前result写入:

source_anchor = "pap['bias_statement'](...)"

这只是说明文字,不包含PAP digest,无法证明报告中的偏差声明绑定的是哪一份冻结PAP。报告虽然显示"来源锚",实际没有可核验锚值。

要求:

result必须记录真实、可验证的PAP绑定,例如:pap_sha256
key="bias_statement"
text原文

pap_sha256须由实际冻结PAP内容确定性计算,不能由调用方自由填写;
canonical算法须明确并与PAP文件对账:排序键、紧凑分隔符、UTF-8、末尾单换行;
运行时添加的_family_trial等非PAP字段不得进入PAP digest;
如调用方另传digest,只能用于与引擎重算值逐字断言;不一致立即fail-closed;
报告"来源锚"必须直接显示实际digest,不得再显示描述性占位文本;
新fixture须证明:PAP v2重算得到2611be36…;
修改任一PAP实质字段会改变digest;
错误digest断言被拒;
仅添加_family_trial不改变冻结PAP digest。

二、listing-age意外层目前被静默放入主判决样本

当前_diagnostic_dimensions()遇到预注册层之外的值,会把它追加为"意外层如实上报"。实测将全部事件标为event_type_layer="unknown"后,引擎仍成功完成顶层判决,并输出:

verdict=SIG
listing-age层=recent_listing/seasoned/unknown

这违反PAP只允许recent_listing/seasoned两层的冻结定义。若未来driver漏标或错标,错误事件仍进入主样本和顶层判决,只是在诊断区多出一个unknown层,属于可改变研究判决的静默旁路。

要求:

exp8启用listing_age诊断时,所有事件的层键必须严格属于:recent_listing
seasoned

None、空字符串、unknown、forecast旧层名及任何白名单外值全部fail-closed;
不得把意外层追加到报告后继续研究;
白名单必须与PAP的diagnostic_dimensions.axes.listing_age逐项一致;
最好在任何CAR计算及顶层_verdict()调用前完成校验;
新攻击fixture须证明:unknown拒绝;
缺失层拒绝;
forecast旧层名拒绝;
合法recent/seasoned放行;
非法层攻击下_verdict()调用次数为0。

三、PAP版本与交付

PAP v2 digest 2611be36…不得覆盖修改。该版本保留并标记"外部复核未通过、未冻结"。

修正后另建PAP v3,至少补入:

PAP digest绑定/报告来源锚规则;
listing-age层白名单外值fail-closed规则。

交付:

PAP v3文件SHA256及canonical digest;
v2→v3逐键diff;
两项攻击测试;
result/report样例中的真实PAP digest;
专项套件和默认路径零回归;
完整diff与边界证明。

继续禁止driver、manifest、冻结、收益读取、正式运行和台账写入。完成后停在交验点,等待人以PAP v3新digest重新下冻结句和新预判。

## 我方接令注记(不改写原文,仅执行性注记)

1. canonical 对账实测(接令即核,只读):PAP v2 文件为单行 canonical JSON+末尾单换行
   (6464 字节);`sha256(canonical串+"\n")` 实测 == 文件 sha `2611be36…`,串本体 sha
   `af21ab71…`(与回修二验收档 §2 一致)。故"重算得到 2611be36"操作化 = 词典序排序键+
   紧凑分隔符(`,`/`:`)+UTF-8+ensure_ascii=False+末尾单换行,顶层 `_` 前缀运行时键
   (如 `_family_trial`)剔除后重算。
2. 状态闸复核(接令即查,只读):exp8=registered/frozen_at 空/result 空;台账 25 行
   =registered18/frozen2/done4/closed1;无 exp8 manifest;两台 HEAD `e689b3c` 净。
3. 触碰面(承继回修二边界+本令):runner/report/fixture/新 PAP v3+标记档+留痕/验收档
   /STATE;禁=driver/读收益/manifest/冻结/写台账/正式运行/改 qbase/重开已裁/无关重构。
4. 回修二其余结论(C1/C3/C6/field_roles/对账 fail-closed 等)= 主体通过,本轮不重开。
