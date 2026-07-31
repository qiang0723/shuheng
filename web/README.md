# 枢衡研究判断平台·静态 Web MVP

本目录提供只读、纯中文的研究展示界面。当前版本只消费仓内静态 fixture，不连接数据库，不提供写入、研究运行或部署能力。

## 页面

- `/`：通俗首页，展示当前结论、方向校准和阅读约束。
- `/experiments`：实验台账，可按生命周期筛选并按名称或编号搜索。
- `/experiments/:id`：实验详情，区分生命周期、统计判决、证据效力与执行边界。

## 本地运行

需要 Node.js 24.14 与 pnpm 11.9。

```bash
pnpm install --frozen-lockfile
pnpm run dev
pnpm run build
pnpm test
pnpm run lint
```

## 数据与边界

- 研究数字来自 `taosha/docs/stage-review-10-experiments-2026-07-31/` 与同日台账快照。
- 静态数据集中在 `lib/fixtures.ts`，显示格式集中在 `lib/format.ts`。
- 页面不得把“未达统计显著”改写为“没有效应”，也不得把预筛选结果写成足额研究证据。
- 当前唯一真实统计显著结果是 exp568，效力仍为智能预筛选；合成冒烟测试不计入正式真实研究。
- 时间统一使用 UTC+8（Asia/Shanghai）。
