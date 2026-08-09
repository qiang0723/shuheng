# Web 静态 MVP · 2026-08-09 快照更新与私有部署交付

- 完成时点：2026-08-09 22:34:44（UTC+8 / Asia/Shanghai）
- 权威数据快照：2026-08-09 22:14:05.537694（UTC+8）
- 部署源码：`0c5efa7e757025c160ef5f79a2128ad72cf507aa`
- Sites 项目：`appgprj_6a788d3439c48191949a10c6b11bd6a3`
- 私有版本：v1（`appgprj_6a788d3439c48191949a10c6b11bd6a3~appgver_d3a3ebe9547c8191b4ec4b7848d3c55f`）
- 生产部署：`appgdep_6a788e87e7748191bde68cd09015a17b`
- 私有地址：<https://shuheng-research.testw348.chatgpt.site>

## 一、只读快照

通过连接级 `default_transaction_read_only=on` 的会话提取当前权威台账、闭卷 result 与校准册；`SHOW transaction_read_only=on`。提取 SQL 与静态结果保存在 `docs/web-snapshot-2026-08-09/`。

- 台账 26 行=`registered 6 / frozen 2 / done 16 / closed 2`；
- 正式真实闭卷研究 15 条，统计显著 1 条，full 效力 4 条且均 `NOT_SIG`；
- 校准册 12 条=`5 命中 / 7 未命中`；
- exp14、exp19 更新为 `done/NOT_SIG` 并载入全精度指标；
- exp18、exp21、exp23 仍 `registered`，exp1、exp6 仍 `frozen`。

全程零数据库写入、零实验状态迁移、零研究运行、零收益读取、零在线 API。

## 二、静态页面与验证

页面 fixture、首页、实验列表、详情页、来源时点及说明文案均更新到本次快照。验证结果：

- `eslint . --ignore-pattern dist --ignore-pattern .next`：PASS；
- 生产 `vinext build`：PASS，路由 `/`、`/experiments`、`/experiments/:id`；
- SSR：4/4 PASS，含 exp14/exp19 详情页；
- 代码规模闸门：PASS（230 文件、34,251 行、978 函数，存量债务 20/50 未增加）；
- 本地生产构建浏览器复核：首页、26 行列表、exp14/exp19 详情页、1280px 与 390px 窄屏均通过，无横向溢出、无控制台错误或警告。

施工中曾直接执行未带项目忽略参数的 `eslint .`，误扫生成目录 `dist/` 后失败；改回 `package.json` 对应的权威命令即通过。该痕迹属于命令口径错误，不是源码缺陷，未据此修改页面规则。

## 三、私有部署

经验证的精确提交先推送 GitHub `origin/main`，再推送 Sites 源仓库；打包件内容哈希=`sha256:134eadec5670dd3f9b80b05c2b835a28666e321ee8717173179ff9b39f4988b1`，41 文件、1,853,440 字节。Sites v1 已部署成功。

访问策略复核：`custom`，仅当前 owner 1 人，允许组 0、外部访客 0。未认证 HTTP 读回为 403，浏览器显示 `Sign in required`，符合私有门预期；未绕过登录或放宽权限。页面内容验收依据为同一提交、同一归档哈希的本地生产构建浏览器实看，生产部署身份由 Sites 版本与提交 SHA 精确绑定。

## 四、停止线

本单元没有数据库写入、在线 API、站内登录功能、后台同步、定时任务或研究运行。exp18/exp21/exp23 语义硬门、exp1/exp6 冻结状态及台账权威状态均未改变。至此停交验点，后续快照更新或功能开发须另令。
