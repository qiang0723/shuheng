# 外审修法 #5 验收档 · addendum result_sha256 库侧锚定(2026-07-13)

依据:`docs/postaudit-five-order-2026-07-13.md` #5(人终签 2026-07-13);施工序第 2 位。

## 1. 现状攻击路径复述(外审描述确认)

`taosha/sql/007` 的 `result_sha256` 是**裸 text 列,库侧零校验**——锚定全靠应用层
(补录 SQL 的前置断言),任意占位串可原样入库,附注所指 result 版本可伪造。
**施工前现场坐实(taosha_app,事务内探针+ROLLBACK)**:INSERT `result_sha256='probe'`
被放行(`addendum_id=9` 返回,已回滚;9/10 为探针 identity 空洞,在案语义)。
既有自检 `verify_addendum.py` 的正向 F1 探针**正是用 'probe' 占位成功入库**——外审点名属实。

## 2. 结构修法

- **文件**:`taosha/sql/009_addendum_sha_anchor.sql`(新迁移,已 apply)。
- **对象**:新函数 `experiment_addendum_bi()` + 新触发器 `trg_experiment_addendum_bi`
  (BEFORE INSERT ON `experiment_addendum`);表结构/既有触发器/数据零触碰。
- **约束语义(不留"忽略或拒绝"二选一)**:
  1. 调用方不传 `result_sha256` → 库从对应 `experiment.result_json` 自动计算填写
     (exp 无 result_json 时留 NULL = 非 result-bound 附注,承 007 注释既有口径);
  2. 显式传入 → 必须与库算值一致,否则拒;
  3. 对应 experiment 无 result_json 时显式传入 → 拒绝创建 result-bound 附注;
  4. 格式约束:64 位**小写**十六进制(`^[0-9a-f]{64}$`),先于一致性判;
  5. 既有正确附注行原样保留(append-only,迁移不触碰行)。
- **实现方式 = BEFORE INSERT 触发器而非表 CHECK**(我方确认点③,随终签批复):
  自动填写需改 NEW 值,CHECK 无此能力;且不做追溯校验。
- **digest 口径唯一(确认点③)**:沿 007 注释既有约定 =
  `sha256(result_json::text jsonb 规范化, UTF8)` hex 小写。
  **施工前实测存量 4 行**(addendum_id 1/4/5/6,锚 e3d2aef9…/c010ce9d…)与库算 digest
  **逐行全等**(id 2/3/7 为回滚探针 identity 空洞,无实行);该断言同时**焊进迁移前置 DO 块**
  ——任一不等迁移即中止(fail-closed apply),apply 实况 DO 通过 = 库内二次证。

## 3. 正向控制

自检 F1–F3 全 PASS:不传 sha 自动填且==库算参照(F1,实测 e3d2aef92bd47c6b…);
显式传正确 sha 放行(F2);无 result 实验(exp1 frozen)不传 sha → 非绑定附注放行、
sha 留 NULL(F3)。既有 append-only 反向 R1–R3 与 Z1(exp3/5 result_json sha 前后同)、
Z2(零残留)全部保持 PASS——合法补录路径(scp+psql 文件法,带正确锚或不带锚)不受扰。

## 4. 反向攻击测试(新增用例)

`verify_addendum.py` 套件 8→**14**,新增:
- **R5** 占位串 `'probe'` 拒(格式约束;外审点名变体,旧自检正向探针翻转为反向用例);
- **R6** 格式合法(64 个 '0')但与 result_json 不一致 → 拒,报错含传入/库算双值;
- **R7** 无 result_json 的实验显式传 sha → 拒 result-bound;
- **R8** 大写十六进制 → 拒(小写口径唯一)。

双幕证据:施工前 'probe' **放行**(§1)→ apply 009 后 R5 **被拒**
(`修法#5: result_sha256 须为 64 位小写十六进制(得到 probe)`)。

## 5. 权限身份 + 迁移与回滚边界 + 验收实物

- **权限身份**:009 以 **postgres 属主** apply;taosha_app 仅 SELECT/INSERT(007 授权不变),
  非属主不能 CREATE OR REPLACE 本触发器函数;探针与套件以 **taosha_app** 跑。
- **迁移边界**:仅新增函数+触发器+前置 DO 断言;零行数据变更;台账/附注实物未扰。
- **回滚边界**:`DROP TRIGGER trg_experiment_addendum_bi; DROP FUNCTION experiment_addendum_bi();`
  表回到 007 态,数据零触碰。
- **验收实物**:
  - 施工 commit **`c5cf38c`**(009 迁移 + 自检重构),push + aliyun ff,两台干净;
  - 自检输出:**`== addendum 自检: 14/14 PASS ==`**(aliyun,taosha_app,2026-07-13);
  - 本项攻击尝试(占位/不一致/越权绑定)**全部被拒**,正反向套件**全 PASS**。
