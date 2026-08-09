# exp14 `ex_div_gap` · persist 与正式闭卷交付

日期：2026-08-09（UTC+8 / Asia/Shanghai）

结论：**exp14 已按既有状态机单事务 persist，终态=`done/NOT_SIG`，正式闭卷。**

## 一、授权与前置断言

- John persist 终令=`ex-div-gap-persist-order-2026-08-09.md`，F-first commit=
  `4f27e06e45fa3da8cb3a44ac0b316e15f8e89fc6`；该 commit 推送并由阿里云 fast-forward
  读回后才进入数据库阶段；
- 主机 Python 首次启动因缺 `psycopg` 在 import 期停止；钉版镜像首次启动因默认用户无权读取
  root-owned `700` 取证脚本而停止。两次均在 Python 业务脚本或数据库连接前退出，失败日志原样保留；
- 随后使用正式运行同一钉版镜像 `shuheng-quant:579a354`，仅以容器 root 读取取证脚本，数据库身份
  仍由 `TAOSHA_APP_DSN/QBASE_APP_DSN` 决定；事务前只读断言=`61/61 PASS`；
- exp14 的 `frozen_at`、双槽空、PAP canonical、manifest432 三处 digest/16键、三件原件 SHA、
  result 关键值与身份水印、递归唯一 verdict、addendum=0、台账 `26=6/3/15/2` 全部精确符合终令。

## 二、唯一写事务

- `taosha_app` 同连接，事务内 `FOR UPDATE` 与原件/状态/PAP/manifest/台账断言=
  `56/56 PASS`；
- 仅走既有状态机
  `ledger.start_running(14) → ledger.finish(14, 已验收result原件) → 一次COMMIT`；
- 事务窗口=`2026-08-09 20:23:00.209391132+08` 至
  `20:23:00.916668760+08`，`done_at=2026-08-09 20:23:00.819510+08`；
- 零研究重跑、零原件覆盖、零报告重渲染、零旁路 SQL、零 addendum、零敏感性分析。

## 三、persist 后核验

后核验=`65/65 PASS`：

- exp14=`done/NOT_SIG`，`frozen_at=2026-08-09 14:33:15.200827+08` 与 PAP 不变；
- 库内 result 与原件 `parsed_equal=True`；canonical result SHA256 双侧均为
  `fda6159be22f562b310086355c0bf0e0c19284586d27cab08741282d20f7c924`，
  库侧 result MD5=`9871f88d47becf1a0bb65a2df0acb7d4`；
- 台账仍26行，分布恰迁为 `registered6/frozen2/done16/closed2`；
- manifest432 三处 digest/content、身份水印、PAP 锚、选择锚、递归唯一 verdict 与 addendum=0
  均保持不变；
- 三件正式运行原件 SHA 保持：result=
  `5ef3a3137b769092bc09b9f0b7cefd0ebc8480f98b4b74193babd9f05ac51a33`、report=
  `8e36af391d33f448e256d614692a88fc6a7d2e66ab1f541d998f777002620a0c`、log=
  `cc5a51cf3f3fe20e3e8b4b07653c684740808111bc777c4ac99e362cf384d730`。

## 四、校准册第十二条

密封原文逐字为「正，把握度60%」，仅押主窗 `[0,+4]` 复权市场调整 CAR 方向，不押幅度或
统计显著性，绑定 PAP digest
`a2eeb653cd490b785783ed066c5e66f5420cd0f3c08e517f1c7cdfd65377cfa7`。
实测主窗 CAAR=`-0.018488168100005337`，故**方向未命中**；累计校准为
**5命中/7未命中**。

## 五、闭卷固定读法

1. 顶层=`NOT_SIG`，不得认定实际高送转除权存在可靠正向或负向异常收益；
2. 朴素 t=`-12.758513063610579`、Corrado=`-9.235338509530482`、日历法=
   `-5.8473913923587775` 虽同向负且名义显著，全部为 `NOT_FOR_VERDICT`，不得引作效应证据；
   簇日相关正是 ADJ-BMP 为唯一判决权威的理由；
3. snapshot375 三值原为冻结前参考，但已由 §7 令与 driver 升格为收益前双层硬闸并两度通过；
4. 通用删失标题“ST=已剔除层”是静态旧措辞；exp14 实际 `st_policy=keep`，ST有效24个事件在主样本内；
5. 主 CAR 使用复权总回报；不得把本结果读作“不复权名义价格幻觉已证实”，raw 跳空与因子比
   仅为 NFV 机械审计；一字板/涨跌停为价格观察，不得读作可成交收益或策略；
6. 效力保持 `llm/prescreen`，不因统计结果升级；行业 unknown 6.04%、剔除率21.61%、N_eff
   坍缩与2024全剔如实保留。

## 六、取证与停止线

- 取证目录=`/root/s14persist/`；`SHA256SUMS` 纳入20件，清单 SHA256=
  `928a8fc9ff9b3fe7ad72500652bbc74835ab740d20d5700b7072bbceaf90a3ac`，逐件校验全过；
- 13类秘密扫描=`TOTAL_HITS=0`；主机缺依赖与容器权限两次启动失败原样入包；
- 阿里云代码 HEAD=`4f27e06e45fa3da8cb3a44ac0b316e15f8e89fc6`，工作树净。

exp14 至此正式闭卷，不再追加复核、重跑、报告重渲染、参数调整或敏感性分析。
