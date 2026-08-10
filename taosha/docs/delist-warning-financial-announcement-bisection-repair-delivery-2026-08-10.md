# exp22 公告索引日期二分窄修 · 本地交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

第二次分页失败的本地最小窄修已经完成。新实现不再消费不稳定的第 2 页及以后内容，而是把每个
自然年确定性递归二分到单页日期叶片，再对每个叶片做两次独立、write-once 读取。规范化行必须
逐字段相等；任何单日仍超页、双读漂移、跨叶重复或越界均 fail-closed。

本轮未推送、未修改阿里云、未重启 `s22-ann-index-v2` 或监督链。远端仍停在 `10/646`，
`metadata_v2_exit=1`，后三阶段零启动。

## 二、实现与证据保全

- 新增 `qbase/ingest/delist_warning_announcement_bisection.py`，只负责区间二分、叶片双读、
  规范化比较与跨叶唯一性；原索引器保留路由、证券/日期校验、write-once、done marker 和最终
  索引职责。
- 当前写入布局固定为
  `raw_pages/<code>/bisect_v3/<year>/<start>_<end>/{probe,confirm}.json`。内部节点只写
  `probe.json`；叶片同时写 probe 与 confirm。
- flat v1、`annual_v2`、`bisect_v3` 三类合法 done marker 均可按各自页树 SHA 自验；新运行只写
  `bisect_v3`。fixture 实证 `annual_v2` 失败件字节不变、合法 marker 继续有效。
- API `totalAnnouncement` 漂移不直接代替正文证据：两读全部计数观测进入叶片审计；至少一个
  观测须命中已双读一致的叶片行数，否则停止。
- v3 中途失败后，既有 probe/confirm 只读恢复；请求或响应结构不符即拒绝，不覆盖后重试。

## 三、攻击验证

```text
verify_delist_warning_announcement_bisection: 17/17 PASS
verify_delist_warning_announcement_index: 39/39 PASS
verify_code_size: PASS; files=240, lines=35678, functions=1064,
  debt_files=20, debt_functions=50
verify_architecture: PASS; modules=171, edges=374, cross_experiment_debts=2
py_compile: PASS
git diff --check: PASS
```

攻击面覆盖：

1. 四日 40 行根区间被确定性拆为两个互斥叶片，根 probe + 两叶双读共 5 件，合并仍为 40 行；
2. 叶片规范化行漂移、`hasMore` 状态漂移、总数两读均不命中分别拒绝；
3. 计数字段漂移但规范化行完全一致且一个观测命中时通过，两项计数均完整保留；
4. 单日仍超页、非终页短读、跨叶片公告 ID 重复分别拒绝；
5. v3 成功请求件只读恢复不重抓，请求被篡改即拒绝；
6. `annual_v2` 失败证据不覆盖，合法 `annual_v2` marker 继续自验；flat v1 marker 的既有 fixture
   同样继续通过。

本地系统 Python 3.9 首次 `py_compile` 因其默认缓存目录不可写而停止，且该解释器也不满足仓内
既有 `X | None` 语法最低版本；随后使用桌面工作区钉定 Python 运行时并把缓存定向 `/tmp`，四件
编译与两套专项均通过。源码未因环境错误放宽。

## 四、停止线与下一步

当前停在本地交付、推送与阿里云续跑授权点。下一步只有在 John 另令后方可：

1. 推送本窄修并由阿里云从同一旧 HEAD 精确 fast-forward；
2. 远端复跑两套专项、路由 fixture、规模/架构闸门及 py_compile；
3. 只读确认旧停止实物仍为 `done=10 / legacy_failed_pages=3 / annual_v2_pages=121 / errors=2`；
4. 以新容器和新监督日志从第 11 票进入 `bisect_v3`，不得删除旧容器、旧页或错误日志；
5. 只有 metadata 646/646 且当前运行零错误，才可按原监督链进入 document materialization →
   UNPROVEN queue → 12 票独立读回。

E1 继续为 `OPEN_FAIL_CLOSED`。本交付不构成公告语义闭合、候选集、G2 起点或冻结资格。
