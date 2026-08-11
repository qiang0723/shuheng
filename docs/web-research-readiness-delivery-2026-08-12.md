# Web 研究就绪度可读性增量交付

时间口径：2026-08-12，Asia/Shanghai（UTC+8）。

## 一、结果

Web 首页现已直接回答“现在能给出股票吗？”：**当前不输出个股候选**。

页面同时解释了边界：现有内容是历史事件研究，不是实时选股系统；唯一正式真实统计显著结果仍为 `llm/prescreen`，四条足额判决研究均未达显著，尚不存在经过冻结的实时个股候选生成器、观察时点、有效期与退出边界。因此本次没有生成或暗示任何股票推荐。

新增“当前研究停点”四卡：

- exp18 `audit_qualified`：首次披露语义证据硬门；
- exp21 `goodwill_impair`：商誉专属减值金额与事件前净资产联合证据硬门；
- exp23 `buyback_announce`：方案身份与用途证据硬门；
- exp22 `delist_warning_financial`：跨期暂停，v1—v8 证据保留，不建立 v9。

## 二、数据身份

两类时点分开显示，未合并为伪“最新”快照：

- 研究结果快照：`2026-08-09 22:14:05.537694（UTC+8）`，继续只消费 `docs/web-snapshot-2026-08-09/`，数字未改；
- 研发状态：`ops/STATE.md` 一百五十一笔，`2026-08-11（UTC+8）`，只用于说明当前停点。

`AppShell` 左下角标签由“数据快照”改为“研究结果快照”，避免把后续研发状态冒充为结果重算。

## 三、触碰面

生产 commit：`0e779d7e70e007ccf3721f12d8d652b2227005df`（`web: explain research readiness`）。

触碰恰七件：本令、Web 首页、专属组件、静态 fixture、样式、SSR 测试与快照标签；净变更 `+122/-3`。零研究代码、零 SQL、零数据库、零在线 API、零登录、零股票列表、零公开部署配置。

## 四、验证

### 4.1 构建与静态门

- ESLint：PASS；
- Vinext production build：PASS；
- SSR：`4/4 PASS`，新增断言覆盖“现在能给出股票吗”“当前不输出个股候选”“历史事件研究，不是实时选股系统”“跨期暂停”“两类时点独立”；
- 规模闸门：PASS，`files=243 / lines=36,180 / functions=1,099 / debt_files=20 / debt_functions=50`；
- 架构闸门：PASS，`modules=173 / edges=378 / cross_experiment_debts=2`。

本机宿主无 Node 运行时，按既有 Docker 路径验证；Dockerfile 的构建阶段强制执行 lint、production build 与 SSR，镜像只有全部通过后才生成。

### 4.2 浏览器显示

在 Codex 内置浏览器对本地 `http://127.0.0.1:3000/` 实测：

- 桌面 `1440×1000`：四张停点卡为两列，页面 `scrollWidth=clientWidth=1440`；
- 窄屏 `390×844`：四张停点卡为单列、宽度均 `308px`，页面与 body 均 `scrollWidth=clientWidth=390`；
- 两种宽度下标题、否定结论、历史研究身份及 exp22“跨期暂停”均可读；
- 浏览器 console warning/error：`0`。

### 4.3 本地私有 Docker

精确 commit 重建并替换既有 loopback 私有服务：

- image：`shuheng-research-web:2026-08-09`；
- image ID：`sha256:ad1b85c86577fdcfd7696ded9eb10f2c7437099d66925708409422de4ccd4d43`；
- OCI revision：`0e779d7e70e007ccf3721f12d8d652b2227005df`；
- image size：`80,791,024` bytes；
- container：`c74be36f26278f263a7ae62fdb2a16be1d64da8dc4786c385e534e3171fa02a0`；
- 状态：`healthy`，用户=`node`，rootfs=`read_only`；
- 唯一宿主映射：`127.0.0.1:3000 -> 3000/tcp`。

HTTP 读回确认首页五个新标记与 `/experiments` 的“26行台账 / 十二条校准 / 实验台账”原内容同时在场。

## 五、边界与停点

本次未调用 Sites 托管：既有人令要求本地 Docker 私有部署，因此保持 loopback 边界，不转公开服务。零数据库写入、零在线 API、零研究运行、零股票推荐、零 exp22 恢复。exp22 跨期暂停与 E1 `OPEN_FAIL_CLOSED` 原裁定不变。

完成停交验点，不自动推送。
