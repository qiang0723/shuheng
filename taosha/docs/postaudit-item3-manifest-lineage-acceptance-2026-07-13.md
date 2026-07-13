# 外审修法 #3 验收档 · manifest 批次血缘一致性(2026-07-13)

依据:`docs/postaudit-five-order-2026-07-13.md` #3(人终签 2026-07-13);施工序第 3 位。

## 1. 现状攻击路径复述(外审描述确认)

`snapshot.collect_content()` 取各批次表 `max(batch_id)` 拼向量,manifest 生成处
(`study_snapshot_biu`)只检"两半在场+非引擎角色"——**无任何血缘交叉校验**:可产出
内部不相容的 manifest(pool_b1_return 批派生自池批 A 而 manifest.pool_b1=B);
三张派生批次表除 `pool_b1_return_batch.pool_batch_id` FK 外无源锚定,qbase 源血缘断链。
**施工前现场坐实(taosha_app,事务内探针+ROLLBACK)**:INSERT
`taosha.pool_b1=999999`(与 pool_b1_return 批 1 的父池批 1 不相容)的 manifest **被放行**
(snapshot_id=3 返回,已回滚;3/4 为探针 identity 空洞,在案语义)。

## 2. 结构修法

**文件**:`taosha/sql/010_manifest_lineage.sql`(已 apply)+ 三 seed + `snapshot.py`。

1. **lineage registry**:新表 `batch_lineage_registry`(append-only 焊死 freeze+no_truncate;
   `UNIQUE(batch_table,batch_id)`;`lineage_status∈{verified,legacy-unverified}`;
   CHECK verified→锚必填;**写权=属主专责,taosha_app/引擎仅 SELECT**)——历史批次唯一合法登记路径。
2. **历史批次物化(不加 NOT NULL,不补猜)**:四个存量派生批(market_batch 1,2 /
   pool_b1_batch 1 / pool_b1_return_batch 1)全部 **verified** 入 registry。
   **证据(查库实测,非补猜)**:qbase 九批全部 `pull_time=2026-07-07` 且此后零新批
   (append-only 时间戳可重构)→ 四批运行时(07-08..07-12)qbase max-batch 向量
   == manifest#1 qbase 半边(digest 2a8a271f…,迁移内前置 DO 断言核对后才登记);
   pool_b1_return 1 的父池批 = 行内 `pool_batch_id=1` FK 实物。锚由**库内 SELECT 构造**
   (manifest#1 的 qbase 半 + source_manifest 指针 + 父池批),evidence_ref 逐批指向
   人签验收档。**legacy-unverified 现役 0 批**(全部可证)。
3. **新派生批次前向强制**:三张批次表加 `source_anchor jsonb` 列(nullable=历史行不失效)
   + 共用 `derived_batch_bi()` BEFORE INSERT 触发器——新行源锚必填,fail-closed。
   三个 seed(`seed_market_return`/`seed_pool_b1`/`seed_pool_b1_return`)落批时写入
   运行时实际所读 qbase 现值向量(复用新抽取的 `snapshot.collect_qbase_vector()`;
   pool_b1_return 另附 `taosha_parent.pool_b1`)。
4. **manifest 生成双检**(`study_snapshot_biu` CREATE OR REPLACE,承 006 原检+digest 库算):
   - **血缘相容(至少强制项)**:`pool_b1_return 批.pool_batch_id == content.taosha.pool_b1`,
     不等即拒(相容性判据,非"所有批次号相等");
   - **血缘可信**:三派生批各须 registry verified **或** 行内 source_anchor 非空
     (`_batch_lineage_trusted()`);legacy-unverified/未登记/不存在 → 拒生成正式研究 manifest。

## 3. 正向控制

- **F1** 现值向量 manifest 生成放行(历史批经 registry 可信;digest 库算 64hex);
- **F2** 带源锚新批落库放行 + manifest 引用该新批放行(前向血缘路径全通);
- **回归**:`verify_study_snapshot --mode probes` **16/16 PASS**(fail-closed 面未扰);
  `verify_integration` **7/7 PASS**,S6 同 manifest 双跑 result sha `3bef1f81…` 逐字节同
  == 在案基线(manifest#2 幂等复用不受新检影响),S7 台账 25 行前后全等。

## 4. 反向攻击测试(新增用例)

新常设自检 `taosha/harness/verify_manifest_lineage.py`,**12/12 PASS**:
- **R1** 血缘不相容拒(施工单反向①):`pool_b1=999999` vs pool_b1_return 批 1 父池批 1 → 拒;
- **R2** 新派生批缺源锚拒(施工单反向②):无 source_anchor 的 market_batch INSERT → 拒;
- **R3** 血缘不可证拒:manifest 引用未登记/不存在批(market_return=999999)→ 拒;
- **R4/R5** taosha_app 写/改 registry → permission denied(登记=属主专责);
- S1–S3 结构断言 + Z1/Z2 零残留。

双幕证据:施工前不相容 manifest **放行**(§1)→ apply 010 后同构造 R1 **被拒**。

## 5. 权限身份 + 迁移与回滚边界 + 验收实物

- **权限身份**:010 以 **postgres 属主** apply;registry 写权仅属主(历史登记走高权限路径,
  与人令"独立 append-only lineage registry"一致);taosha_app/引擎对 registry 仅 SELECT;
  探针与套件以 **taosha_app** 跑(qbase 半经 QBASE_APP_DSN 只读批次表)。
- **迁移边界**:新表+新列(nullable)+触发器+4 行 registry 物化;**现有 manifest#1/#2 行
  与三批次表存量行零触碰**(现有 snapshot 不失效——Z1 断言存量 manifest 数不变)。
- **回滚边界**:DROP 三批次表 BEFORE INSERT 触发器与 `derived_batch_bi()`、
  `_batch_lineage_trusted()`,`study_snapshot_biu()` 重放 006 定义;registry 为 append-only
  审计实物,回滚保留不删;source_anchor 列保留(nullable,无行为)。
- **验收实物**:
  - 施工 commit **`dad1ee0`**(010+三 seed+snapshot 抽取+自检),push + aliyun ff,两台干净;
  - 套件输出:**血缘自检 12/12 PASS** + 回归 **16/16 / 7/7 PASS**(aliyun,2026-07-13);
  - 本项攻击尝试(不相容向量/伪血缘批/越权登记)**全部被拒**,正反向套件**全 PASS**。
