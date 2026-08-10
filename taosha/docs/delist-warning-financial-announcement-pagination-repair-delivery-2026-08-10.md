# exp22 公告索引分页失败 · 最小窄修交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

`000046.SZ` 的分页失败已完成本地最小窄修与攻击验证。修复没有删除总数检查后继续跑超大
区间，而是同时处理已实证的两个官方接口事实：计数字段跨节点不构成一致快照、超大查询第
101 页回卷第 1 页。现改为自然年确定性分片，每个年度仍保留完整性与 fail-closed 门。

本轮**未推送、未更新阿里云代码、未重启容器**；阿里云仍停在原失败实物，后三阶段未启动。

## 二、失败与只读诊断

- 停止时点：`2026-08-10 14:27:22+08`；
- 元数据完成：`10/646`；失败证券：`000046.SZ`；
- 错误：`RuntimeError: 000046 分页总数漂移`；容器 exit=`1`；监督链
  `metadata_exit=1`；
- 失败页三件与 `errors.jsonl`、日志均保留；数据库始终零写入；
- 固定前三页的公告 ID、顺序与时戳在重复读回中逐字相同，但同一轮、跨轮的
  `totalAnnouncement/totalRecordNum` 在 `3841/3845` 间随机切换；
- 第 100 页返回正常历史页；第 101 页及以后回卷到第 1 页内容，证明原全历史单查询不能
  完整越过官方分页上限。

## 三、最小修复

1. 查询区间改为按自然年互斥分片；首尾年按原 `start/end` 截断，并集恰等
   `1991-01-01..2024-06-30`。
2. 每年度最多 100 页；非终页必须恰为 30 行，终页必须关闭 `hasMore`；页内、跨页、跨年
   公告 ID 唯一，证券身份与公告日期必须落在当前年度分片。
3. 不再要求每一页报告相同总数；保存该年度全部计数观测值，年度实际去重行数必须命中其中
   至少一个，否则仍 fail-closed。
4. 新原始页写入版本化布局 `raw_pages/<code>/annual_v2/<year>/<page>.json`；既有页只读恢复，
   请求或响应结构不符即停，不重新请求后覆盖。
5. 新 done marker 显式绑定 `raw_layout=annual_v2` 与递归页树 SHA；旧 marker 无布局字段时仍按
   原平铺目录自验。`000046` 旧失败平铺三页与新布局互不相交。

## 四、验证

```text
verify_delist_warning_announcement_index: 50/50 PASS
verify_code_size: PASS; files=238, lines=35495, functions=1045,
  debt_files=20, debt_functions=50
verify_architecture: PASS; modules=169, edges=372, cross_experiment_debts=2
py_compile: PASS
git diff --check: PASS
```

新增或强化的攻击面包括：

- 计数漂移但页面内容完整时通过，并保留全部计数观测；
- 年度实际行数不命中任何官方计数时拒绝；
- 非终页短页、重复页、年度页数超过安全上限拒绝；
- 自然年分片互斥覆盖、空年度与非空年度合并；
- 已存页只读恢复不重抓，请求被改即拒绝；
- 旧平铺 marker 与新年度 marker 双布局自验。

真实接口只读冒烟使用新代码读取 `000046` 的 `2023-01-01..2023-12-31`，得到：

```text
rows=341 / pages=12 / total observations=[341] / raw_layout=annual_v2
raw_pages_sha256=f912d44ac657b704bdcbffde0a1fd16d33d14524b7256ff514778d5e06592c9e
```

冒烟使用临时目录，完成后清理；零缓存入仓、零数据库访问或写入。

## 五、停止线

当前停在本地窄修验收与推送授权点。下一步只有在 John 另行批准后，才可提交推送、由阿里云
fast-forward 精确读回、复跑专项与治理闸门，并从既有 10 个成功 marker 继续元数据阶段。不得
删除旧失败页或错误日志，不得自动启动后三阶段；只有元数据 646 路由全部完成且当前运行零错误，
监督链才可继续原件物化、合同 UNPROVEN 队列与 12 票独立读回。

E1 仍为 `OPEN_FAIL_CLOSED`；零利润 PIT、终版 PAP、密封、冻结、StudySnapshot、manifest、
收益读取、研究运行或 persist。

## 六、获批推送与阿里云续跑

John 随后逐字批准推送 commits `b58e115`、`299e3a0`，并继续阿里云精确读回、验证及从
既有 `10/646` 检查点续跑，明令不得删除旧失败证据。

- GitHub `origin/main` 已从 `f9c9a3c` fast-forward 至 `299e3a0`；
- 阿里云 `/opt/quant` 工作树先验干净，从同一旧 HEAD 精确 fast-forward 至
  `299e3a0ae80aadc82924d1508864a31ef01cd03b`；
- 远端专项 `50/50`、路由 `6/6`、规模/架构闸门全绿；首次 `py_compile` 因只读源码目录无法
  写缓存而退出，改把缓存指向 `/tmp` 后通过，源码未改；
- 续跑前只读核验：routes=`646`、有效旧 marker=`10`、首待办=`000046.SZ`、旧失败平铺页=`3`、
  新布局页=`0`、错误历史=`1`；
- 新容器 `s22-ann-index-v2` 于 `2026-08-10 15:30:24+08` 启动，使用既有钉版镜像
  `shuheng-quant:579a354`、用户 `shuheng`、只读 rootfs/代码挂载、证据目录唯一可写、无数据库
  凭据；旧失败容器 `s22-ann-index` 保留；
- 新 fail-closed 监督 PID=`772083`，脚本 SHA256=
  `9d46f0689f40904df0eb5bf55bba4de6363628cf7c86c50897ecb8d366bc1c24`；只在前一步 exit 0 时
  依次启动原件物化、合同队列、12 票读回；
- 启动后读回 `done=10 / legacy_failed_pages=3 / annual_v2_pages=16`，证明从首待办的新布局续跑，
  未重抓旧 10 票、未覆盖失败页。

15 分钟 UTC+8 心跳监控已恢复；监控只读，任一阶段非零即报告并暂停，不自动重启。

## 七、v2 续跑第二次 fail-closed

`s22-ann-index-v2` 在 `000046.SZ/2021` 第 7/8 页发现 3 个公告 ID 跨页重复，元数据再次
exit=`1`，监督链记录 `metadata_v2_exit=1`，后三阶段仍未启动。停止后实物为：

```text
done=10
legacy_failed_pages=3
annual_v2_pages=121
errors=2（原总数漂移 + 本次跨页重复）
```

三条重复公告的 ID、时戳和标题在两页逐字相同，不能解释为不同文档复用 ID。旧成功件与旧
失败平铺页均未改动。

随后对 `000046/2021` 做三遍完整年度只读扫描，结果为：

```text
run1: rows=430 / unique=420 / duplicates=10 / totals=[426,430]
      set_sha=a5166cc3597c28fd35ab3fb475edab2bf8a9ed8d348f2366690cd4e6fe64baad
run2: rows=430 / unique=420 / duplicates=10 / totals=[426,430]
      set_sha=fbd5677b4fdf28af3371008c743a85e50904493d57164c0b930b9d96eaa2080e
run3: rows=426 / unique=423 / duplicates=3 / totals=[426,430]
      set_sha=bad6ef333a1dbaf80b5464f77e5427f7a45ba21d216e9453b071520e4f46b28a
```

三遍均有重复且集合 SHA 互不相同，故“年度整段重跑至两遍相同”当前没有收敛证据，直接跨页
去重更会掩盖边界漏项，不得采用。

下一项**未授权提案**仅有一条：从年度开始确定性递归二分日期区间，直到每个叶片在第一次
请求即 `hasMore=false`；每个单页叶片再独立读取两次，只有规范化行逐字相等才接受。任一单日
仍 `hasMore=true`、两读不等、跨叶片 ID 重复或日期越界即 fail-closed。新尝试须另用版本化
布局，永久保留 flat v1 与 annual_v2 两轮失败实物。未经 John 另令不得实施或重启。
