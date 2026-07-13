# 外审修法 #2 验收档 · qbase 快照路由伪造防护(2026-07-13)

依据:`docs/postaudit-five-order-2026-07-13.md` #2(人终签 2026-07-13);施工序第 4 位。

## 1. 现状攻击路径复述(外审描述确认)

`qbase/sql/012` 的 `study_snap_batch()` 读 GUC `shuheng.study_batches`——**引擎连接自报的
完整批次向量 JSON**,qbase 库侧零权威对照(跨库不能直查 taosha manifest)。
**施工前现场坐实(taosha_engine 身份)**:`SET shuheng.study_batches='{完整7键向量}'` 后
`SELECT count(*) FROM explore_reader_calendar_snap` → **8187 行直读成功,零 manifest 参与**
——伪造向量可穿透全部 `_snap` 视图,外审判断属实。taosha 侧 006 按 snapshot_id 查权威表,
无此洞(不对称仅在 qbase 侧)。

## 2. 结构修法

**文件**:`qbase/sql/014_study_snapshot_mirror.sql`(已 apply)+ `taosha/experiment/snapshot.py`
(发布程序)+ `taosha/reader/view.py`(引擎收权)。

1. **权威镜像表** `study_snapshot_mirror(snapshot_id PK, content, digest, created_by, created_at)`:
   append-only(freeze+no_truncate+INSERT 触发器);**digest 由 qbase 触发器权威计算、忽略传值**,
   算法与 taosha 006 逐字同式 = `sha256(content::text jsonb 规范化, UTF8)` hex;拒引擎写入。
2. **发布凭证表** `study_snapshot_publication(publication_id, snapshot_id→mirror FK,
   attested_digest, attested_by, attested_at)`:append-only,**发布=另行 INSERT,不 UPDATE
   镜像行状态位**;INSERT 触发器焊死——无镜像拒、`attested_digest`(受权角色自 taosha 读得的
   证词)≠ 镜像库算 digest 拒 → **两库一致性在库内焊死**。
3. **路由函数收权** `study_snap_batch()` CREATE OR REPLACE:只读 GUC
   `shuheng.study_snapshot_id`(引擎只传 id),路由 = 镜像 JOIN 有效凭证
   (`attested_digest == mirror.digest`),半成品(有镜像无凭证)不可消费;
   **作废:012 的 `shuheng.study_batches` 自报向量路由**。六 `_snap` 视图定义零改动。
4. **发布程序** `snapshot.py::publish()`(受权角色专责,人令①→②→③流程):
   ①创建 taosha manifest(既有)→②qbase 落镜像→③校验两库 content/digest 一致后 INSERT
   attestation;幂等(已发布跳过);镜像 content 与 taosha 不一致 → RAISE,半成品留审计
   不改不删,须另起新 manifest。`--create` 现自动全流程;新增 `--publish N` 回填口。
5. **引擎侧** `ViewReader._connect()`:两库统一只注入 `shuheng.study_snapshot_id`,
   **删除 `_qbase_payload` 自报向量**(不得以任何形式自报批次向量或 token)。
6. **存量回填(确认点①)**:apply 后受权角色执行 `--publish 1` / `--publish 2`,
   镜像 digest 与 taosha 在案值**逐字全等**(`2a8a271f…`/`f660d76b…`)——既是回填,
   也是两库 canonical digest 算法一致的**存量实证**;既有 snapshot 读取无一砖死。

## 3. 正向控制

- **F1**(verify_snapshot_mirror)引擎读已授权且 digest 一致的 snapshot=1 → calendar 8187 行放行;
- **S2** 存量 manifest#1/#2 镜像已回填且 attested,digest==在案值;
- **V1 两库 canonical digest 实测向量验证**(人令硬项):固定测试向量经 qbase 镜像触发器库算
  == taosha 侧同式计算,逐字全等(`558265b7…`);
- **回归**:`verify_integration` **7/7 PASS**,S6 同 manifest 双跑 result sha **`3bef1f81…`
  逐字节同 == 在案基线**——引擎经新路由(镜像+凭证)读出的数据与旧路径逐字节等价,读面零漂移;
  fail-closed 探针套件 16→**19 全 PASS**。

## 4. 反向攻击测试(施工单四条全覆盖)

- **旧 `shuheng.study_batches` 完整伪造 JSON 读取被拒**:P-q3(施工前同构造读穿 8187 行
  → 施工后拒,自报 GUC 失效,路由只认 snapshot_id);
- **不存在的 snapshot ID 被拒**:P-q4(`无有效发布凭证…拒路由`);
- **两库同 ID 但 digest 不一致被拒**:R2(伪证词 0×64 → 拒发布)+ R1(半成品无凭证不可消费)
  + R3(镜像缺失拒发布);
- **引擎零写权**:P-q5/P-q6(镜像/凭证 INSERT → permission denied);R4/R5 append-only UPDATE 拒。

## 5. 权限身份 + 迁移与回滚边界 + 验收实物

- **权限身份**:014 以 **postgres 属主** apply(两表/触发器属主=postgres——写入者 qbase_app
  也拆不掉焊死);**受权角色=qbase_app**(仅 INSERT/SELECT,发布程序身份,配合 taosha_app
  读 manifest);**taosha_engine 对两表仅 SELECT、零写权**;攻击探针以 taosha_engine 跑,
  发布以 qbase_app 跑。
- **迁移边界**:新增两表+触发器+函数替换;012 六 `_snap` 视图与全部底表零触碰;
  taosha 侧零 schema 变更。
- **回滚边界**:`study_snap_batch()` 重放 012 定义(=恢复自报路由,有意降级,须人批);
  mirror/publication 为 append-only 审计实物,回滚保留不删。
- **验收实物**:
  - 施工 commit **`1e1034e`**(014+发布程序+ViewReader 收权+探针+新自检),
    push + aliyun ff,两台干净;
  - 套件输出:**镜像自检 11/11** + **探针 19/19** + **集成回归 7/7(sha 3bef1f81 同基线)**;
  - 本项攻击尝试(自报伪造向量/幽灵 id/digest 不一致/半成品/越权写)**全部被拒**,
    正反向套件**全 PASS**。
