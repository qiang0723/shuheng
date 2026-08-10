# exp22 公告索引 v4 · 单日多页窄修交付

日期：2026-08-10（UTC+8 / Asia/Shanghai）

## 一、结论

本地窄修验收通过。生产改动仅涉及日期二分读取器与公告索引布局常量；新写入固定进入
`bisect_v4`，旧 flat v1、`annual_v2` 与 `bisect_v3` 均只读保留，既有合法 marker 继续自验。

## 二、v4 契约

1. 多日区间继续按日期中点确定性二分；单页叶片继续 pass A/B 独立双读。
2. 单日多页分别完成 pass A 与 pass B：每遍从第 1 页开始，非终页恰 30 行，终页
   `hasMore=false`，最多 100 页。
3. 每遍页内与跨页公告 ID 唯一；证券、公告日与请求区间沿用既有逐页校验。
4. 每遍累计行数须命中该遍至少一个 API `totalAnnouncement` 观测；两遍的逐页计数观测、
   页数与全集行数全部进入叶片审计。
5. 两遍规范化全集经日期、时戳、公告 ID 排序后须逐字段完全相等。任何漂移、重复、短页、
   计数不闭或页数超限均 fail-closed；不存在去重、交并集或重试至一致路径。

## 三、攻击验收

```text
verify_delist_warning_announcement_bisection = 28/28 PASS
verify_delist_warning_announcement_index     = 39/39 PASS
verify_delist_warning_routes                 =  6/6  PASS
verify_code_size = PASS; files=240, lines=35825, functions=1073,
                   debt_files=20, debt_functions=50
verify_architecture = PASS; modules=171, edges=375, cross_experiment_debts=2
py_compile = PASS
git diff --check = PASS
```

新增攻击覆盖稳定两页双遍通过、pass B 内容漂移、跨页重复、非终页短读、缺失计数观测、
任一遍计数不闭、最大页数、v3 失败页不覆盖、v3 合法 marker 自验与 v4 请求件漂移。
规模闸门首次发现 fixture 单函数 72 行并拒绝；拆分为两个职责单一函数后复验通过，业务规则未改。

## 四、续跑边界

John 已授权验收后推送、阿里云精确 fast-forward、远端复验并从合法 `10/646` 检查点启动
全新 v4 容器与监督链。启动前须再次核对 v1/v2/v3 页树、三个旧失败容器、`errors=3` 与
10 个合法 marker 均未变化；v4 只能写新目录。任一远端专项或基线不符即停，不启动跑批。

