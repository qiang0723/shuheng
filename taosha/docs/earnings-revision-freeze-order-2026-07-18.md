# exp20 earnings_revision · PAP v2 冻结令 + 预判密封句(人令原文,2026-07-18 深夜六)

> 人令原文即口径,一字不改转录。绑定 digest = `e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`(即 PAP v2 文件
> `taosha/docs/earnings-revision-pap-final-v2-2026-07-18.json` 的文件 SHA256 == 引擎 canonical 重算值)。
> 旧 digest `94b9ba78…fa17`(v1)未冻结已作废,其表述与预判不得平移(见 NOT-FROZEN 档)。

## 人令原文

外部只读复核通过。批准冻结exp20 PAP v2:
digest=e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5
预判:主窗市场调整后signed CAR为负,即价格总体逆业绩预告修正方向反应(下修后反弹、上修后回吐);把握度55%。
该预判仅表示方向直觉,不预判统计显著性,并只绑定PAP v2 digest e1d18dc1…7fd5;不继承、不平移任何旧版本表述。

一、冻结前即时断言(执行写入前重新只读确认,任一不符立即停止并上报):

- exp20 status=registered;
- result_json、frozen_at、done_at均为空;
- 不存在exp20研究manifest或正式运行记录;
- 台账总行数仍为25;
- v2文件SHA、引擎canonical重算值、冻结令digest三者逐字相等;
- 数据库当前登记PAP仍为未冻结占位载荷。

二、冻结执行:仅走既有状态机合法路径,以应用身份单事务执行registered→frozen:

- 冻结载荷必须是v2 canonical PAP原文;
- 数据库侧重算digest必须等于本令digest;
- 不得手写状态旁路;
- 提交后读回status/frozen_at/pap_json;
- 提交文件SHA、canonical digest、数据库载荷canonical digest、parsed_equal及载荷MD5;
- 台账只更新exp20既有行,不新增行(冻结后分布应为16/3/5/1)。

三、冻结后本单元授权(分段授权,本单元只到行为验收):

- forecast只读视图对及事件生成器最小适配;
- signed统计路径、公告事件顺延及direction诊断轴的必要参数化实现;
- 已预注册14组攻击fixture;
- 12,569/5,225参考数的逐层对账与差异归因(对不上不得修改冻结规则,异常即停报人);
- 全家福回归、既有默认路径零回归证明。

特别验证:

- flat候选正常计数排除,不终止运行;
- flat等非法方向泄漏主事件流时,在CAR与verdict前拒绝;
- signed符号真实作用于事件窗、估计期残差、秩及相关修正输入,不得只改最终CAAR;
- alignment正/负/零/不可得四分支完整;
- direction诊断层递归零verdict、零显著性分类;
- SIG+REVERSED报告不得出现支持性措辞;
- 旧实验默认路径及合成基线逐字节零回归。

本单元仍禁止:正式读取或计算真实收益结果;生成正式研究manifest;正式运行事件研究;persist或写入result_json。
完成代码与fixture验收后停交验点;通过外部只读复核后,再另行授权manifest与单次正式运行。

## 留痕说明(工程侧,非令文)

- 预判密封句(仅方向直觉,不预判显著性,只绑本 digest):**主窗市场调整后 signed CAR 为负(下修后反弹、上修后回吐),把握度 55%**。开封对照仅在 persist 后校准读数入册,原文永不改述。
- 冻结前断言、冻结执行与读回验收另立验收档 `earnings-revision-freeze-acceptance-2026-07-18.md`。
- 冻结后台账预期分布 16/3/5/1 = registered 16 / frozen 3 / done 5 / closed 1(当前 25 行 = 17/2/5/1,exp20 一行迁态,零新增零删除)。
