# exp11 high_pullback PAP 冻结令 + 预判绑定 + 冻结后最小适配授权 · 人令原文留痕(2026-07-24 五)

> 人令下达 2026-07-24(同日第五令);原文即口径,一字不改。F 条留痕 commit 先行,与施工分单。
> 分段授权至行为验收止;正式收益读取/正式 manifest/正式运行/persist 仍禁止,行为验收停交验点,外部复核通过后另令。

---

枢衡工地:

批准冻结exp11 high_pullback终版PAP:
digest=eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc

预判:主窗市场调整后CAR为正,把握度60%。
该预判仅押方向、不押幅度、不预判统计显著性;仅绑定上述终版digest,不继承、不平移任何旧版本表述。

一、冻结前只读确认(任一不符立即停止并上报):

exp11 status=registered,frozen_at/result_json/done_at均空;
无exp11正式manifest或运行记录;
终版文件SHA、引擎canonical重算值、本令digest三者逐字相等;
数据库当前登记PAP仍为未冻结占位载荷;
台账25行,分布14/2/8/1。

二、冻结执行:既有状态机,taosha_app同连接单事务registered→frozen(FOR UPDATE再断言);冻结载荷=终版canonical原文,不得改写、复制草案或运行时补键;DB侧重算digest必须==本令digest。读回status/frozen_at/pap_json,交canonical/parsed_equal/载荷MD5;台账仅迁exp11既有行,冻结后分布应为13/3/8/1。

三、冻结后本单元授权(分段授权,至行为验收止):

事件生成器与driver最小适配(常规四件,missing_bar_only引擎路径已收编无需再扩);
攻击fixture:锚重置(连续新高只留末锚)/首触即决三分支(EVENT/MA_KILL/DEEP_KILL)/闭区间边界(恰-3%/恰-5%)/期内无bar=NO_TOUCH/右界TRUNCATED/事件键唯一/digest与engine_params逐字消费/"价格观察日"术语渲染;
漏斗按冻结规则复现,42,719作双跑参考,差异按血缘归因,不追数不改规则;
全家福+既有默认路径零回归。

仍禁止:正式收益读取、生成正式manifest、正式运行、persist。行为验收停交验点,外部复核通过后另令。
