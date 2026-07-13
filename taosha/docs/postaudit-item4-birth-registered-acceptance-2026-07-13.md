# 外审修法 #4 验收档 · 状态机出生即 frozen 旁路封死(2026-07-13)

依据:`docs/postaudit-five-order-2026-07-13.md` #4(人终签 2026-07-13);施工序第 1 位。
统一交付 5 要素逐项如下。

## 1. 现状攻击路径复述(外审描述确认)

`taosha/sql/005_experiment_statemachine.sql` 的 `experiment_biu()` 出生态白名单为
`('registered','frozen')`,且第 42-44 行要求 frozen 出生**配套** `frozen_at`——即
taosha_app 常规写路径可 INSERT 一条出生即 frozen 的实验行,**绕过 registered→frozen
的人冻结仪式**(冻结=人对 PAP 的终审动作;出生即 frozen 等于登记方自我宣告已冻结,
且该行的 pap_json 依铁律④立即不可改,伪造冻结口径成立)。

**施工前现场坐实(taosha_app 身份,事务内探针+ROLLBACK 零残留)**:
INSERT `status='frozen', frozen_at=now()` 被放行,`RETURNING` 得
`exp_id=44 / status=frozen / has_frozen_at=t`,随即回滚。既有 44 用例自检
恰无此变体(R28 只测 registered+frozen_at)——外审指认的覆盖缺口属实。
(探针消耗 identity 序号 44 不可回退,属在案空洞语义,随 Q4 纸面稿注明的既有约定。)

## 2. 结构修法

- **文件**:`taosha/sql/008_birth_registered_only.sql`(新迁移,已 apply)。
- **对象**:`CREATE OR REPLACE FUNCTION experiment_biu()`(仅此函数;触发器绑定、
  `experiment_bu()` 及表结构零触碰)。
- **约束变化**:
  1. 出生态唯一合法值 `registered`(005 白名单中的 `frozen` 作废——函数 COMMENT 显式作废旧口径);
  2. `frozen_at` 出生必空(吸收并收紧 005 的"registered 出生不得带 frozen_at",对一切出生态成立);
  3. 保留:family_trial 触发器自增 / 铁律① llm→prescreen / result_json、done_at、closure_reason 出生必空。
- **历史导入边界(人令原文)**:历史导入需求走独立高权限迁移程序(superuser 专项脚本+留痕),
  不复用 taosha_app 常规写路径。**本次无历史导入需求,该程序不预建**,需求出现时另行人批。

## 3. 正向控制(合法路径仍正常)

- 仓内唯一登记路径 `taosha/experiment/ledger.py::register()` 不写 status(库默认 registered)、
  `freeze()` 走 UPDATE registered→frozen 迁移——**代码零改动、行为零影响**。
- 自检套件正向用例 F1–F10b(INSERT registered 放行 / registered→frozen→running→done 全链 /
  registered→closed / frozen→closed / PAP registered 态完善 / set_meta 三态不误伤)**全 PASS**。

## 4. 反向攻击测试(新增用例)

`taosha/experiment/verify_state_machine.py` 新增(套件 44→**46**):
- **R31** INSERT 出生即 frozen+frozen_at(外审 #4 变体,005 曾放行)→ 拒,报错
  `修法#4: INSERT 出生态仅允许 registered(得到 frozen…)`;
- **R32** INSERT 出生即 frozen 缺 frozen_at → 拒(同上白名单)。

现场双幕证据:施工前探针**放行**(§1)→ apply 008 后同一探针**被拒**(ERROR 修法#4,
line 15 RAISE),回滚后 `family LIKE '_probe_postaudit%'` 行数 = **0**(零残留)。

## 5. 权限身份 + 迁移与回滚边界 + 验收实物

- **权限身份**:008 以 **postgres 属主** apply(`sudo -u postgres psql -d taosha -f`);
  apply 后实测 `experiment_biu()` proowner = `postgres`——taosha_app 无 CREATE OR REPLACE
  权(非属主),不能自行放宽本约束;反向探针与全套自检均以 **taosha_app** 身份跑。
- **迁移边界**:仅 `CREATE OR REPLACE experiment_biu()` + COMMENT;台账数据零触碰,
  台账 25 行未扰(自检整体 ROLLBACK + Z1 零残留断言)。
- **回滚边界**:回滚 = 重放 005 中同名函数定义(触发器绑定不变);无 schema 变更需回退。
- **验收实物**:
  - 施工 commit **`8cd2040`**(008 迁移 + 自检 R31/R32),push + aliyun ff,两台干净;
  - 自检输出:**`== 状态机自检: 46/46 PASS ==`**(aliyun,taosha_app 身份,2026-07-13);
  - 本项攻击尝试(出生即 frozen 直插)**被拒**,正反向套件**全 PASS**。
