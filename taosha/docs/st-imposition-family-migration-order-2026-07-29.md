# exp15 `st_imposition` · family不可变迁移令（2026-07-29）

> 人授权原文：“批准”。上下文唯一指向：批准关闭exp15，并以`delist_warning_financial` family trial 2重新登记承接；迁移后继续PAP草案。

## 一、原因与裁定

人已裁：exp15与exp12独立family；exp15与exp22同族；当前推进的ST实施事件按trial 2、族内α=`0.05/2=0.025`。

数据库中exp15现为`st_imposition/trial 1`，exp22为`delist_warning_financial/trial 1`；`family/family_trial`为不可变列，禁止旁路修改。不得在PAP或driver中伪造trial 2。

## 二、前置只读断言

1. exp15=`registered`，三槽空，无manifest/addendum/运行产物；
2. exp22=`registered`、`family=delist_warning_financial`、`family_trial=1`；
3. 台账25行=`registered 11 / frozen 2 / done 11 / closed 1`；
4. 本次迁移前Git与数据库无其他未决操作。

任一不符立即停止。

## 三、单事务迁移

以`taosha_app`同连接单事务：

1. `FOR UPDATE`锁定exp15与exp22并重做前置断言；
2. `ledger.close(15, reason)`，关闭原因固定为：`人裁2026-07-29：与exp22 delist_warning_financial同族；family/family_trial不可变，旧exp15未冻结无产物，关闭后由新登记trial 2承接。`；
3. 复制旧exp15的title/source_type/verdict_power/contamination_note/pap_json/data_class/crowding_prior，仅将family改为`delist_warning_financial`，走`ledger.register`既有通路；
4. 触发器必须自动返回`family_trial=2`，新exp_id以数据库返回值为准；
5. 一次COMMIT。不得手写family_trial、不得UPDATE不可变列、不得旁路SQL。

## 四、后核验与边界

- 旧exp15=`closed`且closure_reason逐字相等；新行=`registered`、trial 2、三槽空；
- 新旧除family/trial/状态字段外的登记内容解析相等；
- 台账应为26行=`registered 11 / frozen 2 / done 11 / closed 2`；
- exp22保持registered/trial 1不变；
- 零PAP冻结、零manifest、零收益读取、零正式运行、零persist。

迁移核验通过后，PAP草案仅以新exp_id为对象；文档仍以“exp15旧行/新承接行”明确区分，不抹除历史。
