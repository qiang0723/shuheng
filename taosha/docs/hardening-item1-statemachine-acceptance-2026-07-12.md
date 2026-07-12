# 硬化① 台账状态机焊死 · 验收档(2026-07-12)

> 依据:`docs/hardening-window-order-2026-07-12.md` ①(人批终版 2026-07-12)。
> 修法原文:result 仅可随 running→done 首写;frozen_at 仅可随 registered→frozen 写;done_at 仅可随迁移写——字段变更绑定唯一合法迁移。

## 1. 裁决留痕(施工中人拍)

**人拍 A(2026-07-12,closed 关闭原因载体)**:施工单字面(result 仅随 running→done)与既有 `ledger.close()` 行为(把 `{"closure": reason}` 写入 result_json,exp2 实物如此)打架,上报三选项,人拍 **A = 严格字面 + 新列**:
- result_json 仅绑 running→done;
- `close()` 停写 result_json,台账新增 `closure_reason text` 列(仅可随 registered/frozen→closed 迁移一次性写,同款焊死);
- **exp2 历史行(closed 且 result_json 装 closure)原样保留不动**,触发器只辖此后变更。

## 2. 修法实物

- **迁移 `taosha/sql/005_experiment_statemachine.sql`**(commit `7a1520e`,已 apply 属主 postgres,2026-07-12):
  - `experiment_bu()`(BEFORE UPDATE)重写:字段变更绑定唯一合法迁移——
    - `frozen_at` 变更 ⇔ 仅 `OLD.frozen_at IS NULL AND registered→frozen`;
    - `result_json` 变更 ⇔ 仅 `OLD.result_json IS NULL AND running→done`(一次性首写);
    - `done_at` 变更 ⇔ 仅一次性且随 `running→done` 或 `registered/frozen→closed` 迁移;
    - `closure_reason` 变更 ⇔ 仅一次性且随 `registered/frozen→closed` 迁移(人拍A);
    - `pap_json` 仅 registered 态(未冻结)可完善(铁律④原义保持并收紧到态);
    - status 白名单迁移(registered→frozen|closed, frozen→running|closed, running→done)不变;
    - 迁移完备性:进 frozen 须带 frozen_at;进 done 须带 result_json+done_at;进 closed 须带 closure_reason+done_at。
  - `experiment_biu()`(BEFORE INSERT)加**出生焊死**(见 §5 工程加固上报):出生态仅 registered/frozen;result_json/done_at/closure_reason 出生必空;registered 出生不得带 frozen_at。铁律①(llm→prescreen)、family_trial 自增原义不变。
- **`taosha/experiment/ledger.py`**:`close()` 改写 `closure_reason`(不再写 result_json);模块头三行注释补齐(宪章第6条)。
- **自检件 `taosha/experiment/verify_state_machine.py`(常设,宪章第7条)**:验收 (a)(b) 两组用例固化。机制=以 **taosha_app** 身份、单事务+逐用例 SAVEPOINT+末尾整体 ROLLBACK,对台账零残留(结尾断言探针 family 行数=0)。

## 3. 验收(a) 反向:非法路径全拒(taosha_app 实测,2026-07-12)

自检 30 条反向用例**全拒**(R1–R30),逐条覆盖人令清单:
- registered 态写 result(R1)/ 提前写 frozen_at(R2)/ 跳态迁移(R3 registered→running、R4 registered→done、R12 frozen→done、R14 running→closed、R18 done→running、R23 closed→running);
- 二次写各字段:frozen_at(R11)、result_json(R19)、done_at(R20)、closure_reason(R22);
- 绕态改 done_at:registered 态(R7)、running 态(R16);
- 各态非迁移写 result:registered(R1)、frozen(R13)、running(R15)、closed(R21);
- 完备性:→frozen 缺 frozen_at(R9)、→done 缺 result(R17)、→closed 缺 closure_reason(R5);
- 出生焊死:INSERT 即 done 带 result(R24)/running(R25)/closed(R26)/registered 带 result(R27)/带 frozen_at(R28);
- 既有回归:不可变列(R8)、pap 冻结后改(R10)、铁律① llm+full(R29)、DELETE(R30,权限层 permission denied 先拒=双层任一)。

## 4. 验收(b) 正向:合法流程全通(同跑实测)

10 条正向用例全通:INSERT 登记(F1)→ registered 态 PAP 正常完善(F2)→ set_meta 类字段各态不误伤(F3 registered/F5 frozen/F8 done)→ registered→frozen→running→done 全程走通(F4/F6/F7)→ registered→closed 走通(F9)→ frozen→closed 走通(F10a/b)→ **合法完成后 result 仍拒二次写**(R19,b 组硬项)。

**终跑 44/44 PASS**(S1/S2 结构断言 + 30 反向 + 10 正向 + Z1 零残留 + F1)。运行方式:aliyun `python -m taosha.experiment.verify_state_machine`(TAOSHA_APP_DSN)。

## 5. 工程加固上报(超字面部分,请架构窗口随验收确认)

**出生焊死(INSERT 白名单)**:人令修法只述 UPDATE 迁移;但若 INSERT 可出生即 done/closed 带 result,则"result 仅可随 running→done 首写"存在结构绕道。已焊:出生态仅 registered/frozen、绑定字段出生必空。影响面:创始转录式 INSERT(seed_founding 直插 closed 带 result,exp2)此后结构上不可复现——该脚本为一次性历史件,不再需要;新登记(收割会式)与 persist 全链不受影响(实测 F 组)。**如架构窗口否此加固,回滚点=单独放宽 biu,不牵动 bu。**

## 6. 过程留痕(自检自身缺陷修正)

首跑 42/44:R11/R20"二次写被放行"——探针用 `now()` 写入,而 `now()` 同事务内恒定 → 写入值与原值相同 → `IS DISTINCT FROM` 判无变更(无害 no-op),**触发器无过,探针有过**。修正=二次写探针改 `now()+interval '1 day'`(commit `9d35e81`),重跑 44/44。留痕以示未粉饰。

## 7. 已知副作用登记

- **exp_id identity 序号消耗**:探针 INSERT(含被拒条)烧 identity 序号且不随回滚退回;每跑一次自检约消耗 9 个序号(本轮两跑后 last_value=43,台账仍 25 行)。exp_id 出现空洞属 PG 固有行为,**台账以行存在为准**,非数据缺失。
- 台账实物核对(2026-07-12 跑后):25 行 =registered18/frozen3/done3/closed1 不变;exp2(closed,历史 result_json 保留,closure_reason=NULL)、exp3/exp5(done,result 在)逐一原样。

## 8. 结论

硬化① 修法+验收(a)(b) 全过,用例已固化常设自检。**待架构窗口验收后进 ③**(②可并行,已另行开工)。
