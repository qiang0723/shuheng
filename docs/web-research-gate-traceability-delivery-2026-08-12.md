# Web 研究停点可追溯增量交付

时间口径：2026-08-12，Asia/Shanghai（UTC+8）。

## 一、结果

主页“当前研究停点”四张卡现在均可进入对应实验详情：exp18、exp21、exp22、exp23。

这四个详情页新增“当前研究停点”区块，逐字显示静态 fixture 已登记的硬门/暂停状态与原因。exp22 继续显示“跨期暂停”和“官方公告分页集合发生漂移；v1—v8 证据保留，不建立 v9”，未提供替代源、代理证据或恢复建议。

## 二、时点与语义边界

详情页并列显示但不混写：

- 研发状态：`STATE 一百五十一笔，2026-08-11（UTC+8）`；
- 研究结果快照：`2026-08-09 22:14:05.537694（UTC+8）`。

区块固定注明：只解释研发停点，不构成统计结果、代理证据或恢复授权。既有实验生命周期、判决、校准数字与 provenance 文件均未修改。

## 三、触碰面

生产 commit：`aaa7f05251d20bd8934836d584f777d032750d61`（`web: trace research gate status`）。

触碰恰六件：本令、主页停点组件、实验详情页、静态 fixture helper、专属样式、SSR 测试；净变更 `+82/-5`。零研究代码、零 SQL、零数据库、零在线 API、零登录、零实验状态、零股票列表、零公开部署。

## 四、验证

- ESLint：PASS；
- Vinext production build：PASS；
- SSR：`5/5 PASS`，新增 `/experiments/22` 的停点、状态、双时点和禁止代理断言；
- 规模闸门：PASS，`files=243 / lines=36,211 / functions=1,099 / debt_files=20 / debt_functions=50`；
- 架构闸门：PASS，`modules=173 / edges=378 / cross_experiment_debts=2`；
- 本地 HTTP 读回：首页精确存在 `/experiments/18`、`/21`、`/22`、`/23` 四链接；exp22 详情精确命中“当前研究停点 / 跨期暂停 / 官方公告分页集合发生漂移 / 两类时点独立 / STATE 一百五十一笔”。

## 五、本地私有 Docker

- image：`shuheng-research-web:2026-08-09`；
- image ID：`sha256:61db52551075456069f26473c68fbd679affa45766efffc0af9901eeeb5cde58`；
- OCI revision：`aaa7f05251d20bd8934836d584f777d032750d61`；
- image size：`80,791,387` bytes；
- container：`ddb9b03035c6cb3030fe93ba7638b288a0b4865997eaeeaef45512b2d058ba4f`；
- 状态：`healthy`，用户=`node`，rootfs=`read_only`；
- 唯一宿主映射：`127.0.0.1:3000 -> 3000/tcp`。

保持既有本地 Docker 私有部署；未调用 Sites 托管。exp18/21/23 硬门与 exp22 跨期暂停均未恢复。完成停交验点，不自动推送。
